# Run multiple scraping scripts concurrently
import subprocess

scripts = ["indeed_scraping.py", "linkedin_scraping.py", "pracuj_scraping.py"]

# Run the scripts concurrently
processes = []
for script in scripts:
    command = ["python", script]
    processes.append(subprocess.Popen(command))
 
# Wait for all processes to finish
for process in processes:
    process.wait()