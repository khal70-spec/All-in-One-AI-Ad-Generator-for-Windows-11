import inspect


def make_step_kwargs(pipe, num_steps, progress_callback, base=10, span=70):
    """Return kwargs to pass to a diffusers pipeline for per-step progress.

    Diffusers pipelines report progress in two different ways depending on
    version: the classic ``callback``/``callback_steps`` pair, or the newer
    ``callback_on_step_end`` (Mochi / HunyuanVideo / LTX-Video). We inspect
    the pipeline signature so we only pass what it actually accepts — if it
    supports neither, we return ``{}`` and the coarse progress is kept.
    """
    if progress_callback is None or pipe is None:
        return {}
    try:
        params = inspect.signature(pipe.__call__).parameters
    except Exception:
        return {}

    if "callback_on_step_end" in params:
        def cose(pipe_obj, step_index, timestep, callback_kwargs):
            frac = (step_index + 1) / max(num_steps, 1)
            try:
                progress_callback(base + span * frac,
                                  f"Generating... step {step_index + 1}/{num_steps}")
            except Exception:
                pass
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
            frac = step / max(num_steps, 1)
            try:
                progress_callback(base + span * frac,
                                  f"Generating... step {step}/{num_steps}")
            except Exception:
                pass
        return {"callback": cb, "callback_steps": 1}

    return {}
