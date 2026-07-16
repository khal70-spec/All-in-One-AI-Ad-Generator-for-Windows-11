import inspect


class GenerationCancelled(Exception):
    """Raised inside a diffusers callback when the user requests cancel."""


def make_step_kwargs(pipe, num_steps, progress_callback, base=10, span=70,
                     cancel_check=None):
    """Return kwargs to pass to a diffusers pipeline for per-step progress.

    Diffusers pipelines report progress in two different ways depending on
    version: the classic ``callback``/``callback_steps`` pair, or the newer
    ``callback_on_step_end`` (Mochi / HunyuanVideo / LTX-Video). We inspect
    the pipeline signature so we only pass what it actually accepts — if it
    supports neither, we return ``{}`` and the coarse progress is kept.

    ``cancel_check`` (optional) is a zero-arg callable; when it returns a
    truthy value a :class:`GenerationCancelled` is raised inside the
    pipeline callback, aborting the diffusion loop between steps.
    """
    if progress_callback is None and cancel_check is None:
        return {}
    if pipe is None:
        return {}
    try:
        params = inspect.signature(pipe.__call__).parameters
    except Exception:
        return {}

    def _tick(step_index, total):
        if cancel_check is not None and cancel_check():
            raise GenerationCancelled("Cancelled by user")
        if progress_callback is None:
            return
        frac = (step_index) / max(total, 1)
        try:
            progress_callback(base + span * frac,
                              f"Generating... step {step_index}/{total}")
        except Exception:
            pass

    if "callback_on_step_end" in params:
        def cose(pipe_obj, step_index, timestep, callback_kwargs):
            _tick(step_index + 1, num_steps)
            return callback_kwargs
        return {"callback_on_step_end": cose}

    if "callback" in params:
        def cb(*args):
            step = None
            if args:
                a0 = args[0]
                step = a0 if isinstance(a0, int) else getattr(a0, "step", None)
            if step is None:
                return
            _tick(step, num_steps)
        return {"callback": cb, "callback_steps": 1}

    return {}
