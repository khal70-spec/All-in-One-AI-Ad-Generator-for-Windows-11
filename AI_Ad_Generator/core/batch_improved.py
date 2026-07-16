import os
import json
import threading
from typing import Optional, Callable, Dict, Any, List
from .logger import get_logger
from .progress import GenerationCancelled

log = get_logger("batch")


class BatchProcessor:
    """Process multiple generation jobs in sequence with progress tracking.
    
    Supports cancellation, error recovery, and detailed reporting.
    """

    def __init__(self, model_manager, text_to_video_gen=None, image_to_video_gen=None):
        self.model_manager = model_manager
        self.text_to_video_gen = text_to_video_gen
        self.image_to_video_gen = image_to_video_gen
        self.is_running = False
        self.cancel_requested = False
        self.current_job = 0
        self.total_jobs = 0

    def cancel(self) -> None:
        """Request batch cancellation."""
        self.cancel_requested = True
        log.info("Batch cancellation requested")

    def _check_cancel(self) -> None:
        """Check if cancellation was requested.
        
        Raises:
            GenerationCancelled: If cancel was requested
        """
        if self.cancel_requested:
            raise GenerationCancelled()

    def process_batch(self, jobs: List[Dict[str, Any]], 
                     progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Process a batch of generation jobs.
        
        Args:
            jobs: List of job dictionaries
            progress_callback: Callback for overall progress
            
        Returns:
            Summary dictionary with results and statistics
        """
        if not jobs or not isinstance(jobs, list):
            raise ValueError("Jobs must be a non-empty list")

        self.is_running = True
        self.cancel_requested = False
        self.total_jobs = len(jobs)
        self.current_job = 0
        
        results = {
            "total_jobs": self.total_jobs,
            "completed": 0,
            "failed": 0,
            "cancelled": False,
            "jobs": [],
            "errors": [],
        }

        try:
            # Verify disk space before starting
            from config import OUTPUTS_DIR
            if not self.model_manager.check_disk_space(OUTPUTS_DIR, min_gb=1.0):
                raise RuntimeError("Insufficient disk space for batch processing")

            for job_index, job in enumerate(jobs):
                if self.cancel_requested:
                    results["cancelled"] = True
                    break

                self.current_job = job_index + 1
                job_result = self._process_job(job, progress_callback)
                results["jobs"].append(job_result)

                if job_result.get("success"):
                    results["completed"] += 1
                else:
                    results["failed"] += 1
                    if "error" in job_result:
                        results["errors"].append({
                            "job_index": job_index,
                            "error": job_result["error"]
                        })

                # Clean up after each job
                self.model_manager.cleanup_cache()

        except Exception as e:
            log.error("Batch processing error: %s", e)
            results["errors"].append({"batch_error": str(e)})
        finally:
            self.is_running = False
            if progress_callback:
                progress_callback(100, f"Batch complete: {results['completed']}/{self.total_jobs} succeeded")

        return self._save_batch_summary(results)

    def _process_job(self, job: Dict[str, Any], 
                    progress_callback: Optional[Callable]) -> Dict[str, Any]:
        """Process a single batch job.
        
        Args:
            job: Job configuration dictionary
            progress_callback: Callback for progress updates
            
        Returns:
            Job result dictionary
        """
        try:
            if not isinstance(job, dict):
                return {"success": False, "error": "Invalid job format"}

            job_type = job.get("type")
            if job_type not in ["text_to_video", "image_to_video"]:
                return {"success": False, "error": f"Unknown job type: {job_type}"}

            # Update progress
            if progress_callback:
                progress = int((self.current_job / self.total_jobs) * 100)
                progress_callback(progress, f"Processing job {self.current_job}/{self.total_jobs}")

            if job_type == "text_to_video":
                return self._process_text_to_video(job)
            else:
                return self._process_image_to_video(job)

        except GenerationCancelled:
            return {"success": False, "error": "Cancelled by user"}
        except Exception as e:
            log.error("Job processing failed: %s", e)
            return {"success": False, "error": str(e)}

    def _process_text_to_video(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Process a text-to-video job.
        
        Args:
            job: Job configuration
            
        Returns:
            Job result dictionary
        """
        try:
            if not self.text_to_video_gen:
                return {"success": False, "error": "Text-to-video generator not initialized"}

            required_params = ["prompt", "model"]
            if not all(param in job for param in required_params):
                return {"success": False, "error": f"Missing required params: {required_params}"}

            output_path = self.text_to_video_gen.generate(
                prompt=job["prompt"],
                negative_prompt=job.get("negative_prompt", ""),
                num_frames=job.get("num_frames", 24),
                width=job.get("width", 512),
                height=job.get("height", 512),
                num_steps=job.get("num_steps", 25),
                guidance_scale=job.get("guidance_scale", 7.5),
                seed=job.get("seed", -1),
                model=job["model"],
                cancel_check=self._check_cancel,
            )
            return {"success": True, "output_path": output_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _process_image_to_video(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Process an image-to-video job.
        
        Args:
            job: Job configuration
            
        Returns:
            Job result dictionary
        """
        try:
            if not self.image_to_video_gen:
                return {"success": False, "error": "Image-to-video generator not initialized"}

            required_params = ["image_path", "model"]
            if not all(param in job for param in required_params):
                return {"success": False, "error": f"Missing required params: {required_params}"}

            if not os.path.exists(job["image_path"]):
                return {"success": False, "error": f"Image not found: {job['image_path']}"}

            output_path = self.image_to_video_gen.generate_from_image(
                image_path=job["image_path"],
                num_frames=job.get("num_frames", 25),
                num_steps=job.get("num_steps", 25),
                motion_bucket_id=job.get("motion_bucket_id", 127),
                noise_aug=job.get("noise_aug", 0.02),
                seed=job.get("seed", -1),
                model=job["model"],
                cancel_check=self._check_cancel,
            )
            return {"success": True, "output_path": output_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _save_batch_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Save batch summary to JSON file.
        
        Args:
            results: Batch results dictionary
            
        Returns:
            Results dictionary with summary file path
        """
        try:
            import time
            from config import OUTPUTS_DIR
            
            timestamp = int(time.time())
            summary_path = os.path.join(OUTPUTS_DIR, f"batch_summary_{timestamp}.json")
            
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            results["summary_path"] = summary_path
            log.info("Batch summary saved: %s", summary_path)
        except Exception as e:
            log.warning("Could not save batch summary: %s", e)

        return results
