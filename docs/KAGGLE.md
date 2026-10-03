# Optional Kaggle execution

No Kaggle account or API token is required for the demonstrated CPU path. This project has not uploaded any private capture or used the provided credential. Hosted GPU execution remains unvalidated until an actual run is recorded.

1. Create a private Kaggle dataset containing the project source, the intended captures and (optionally) downloaded models. Keep credentials out of the dataset. Uploading the raw home imagery is your explicit choice.
2. Create a private notebook, enable a GPU and Internet for dependency/model downloads. Copy the project from its read-only dataset mount into `/kaggle/working/Astra_Project`.
3. Keep Kaggle's GPU-compatible PyTorch; install the remaining pinned requirements. Verify `torch.cuda.is_available()` before selecting CUDA. Do not run the CPU-wheel installation command from `setup.sh` in a GPU notebook.
4. Fetch any missing public weights. Then run the same CLI with `--device cuda --depth-model depth-pro`. Dynamic int8 is CPU-only; use float32 Depth Pro on CUDA. Use `.venv/bin/python` on the laptop, the notebook's `python` on Kaggle.
5. Download the complete run directory, including JSON, figures, timing, provenance and hashes. Record accelerator type and software versions. CPU and GPU runtimes must not be mixed in the timing table.

Example notebook shell cells (edit the dataset mount):

```python
from pathlib import Path
import shutil
source = Path('/kaggle/input/YOUR_PRIVATE_DATASET/Astra_Project')
work = Path('/kaggle/working/Astra_Project')
shutil.copytree(source, work, dirs_exist_ok=True)
```

```bash
cd /kaggle/working/Astra_Project
python -m pip install -r requirements.txt transformers==4.57.1 timm==1.0.20 'huggingface-hub>=0.34,<1'
python scripts/fetch_models.py --depth-pro
python scripts/fetch_semantic_models.py
python -m astra run --tier photos --input three_room --output runs/kaggle_photos --device cuda --depth-model depth-pro
```
