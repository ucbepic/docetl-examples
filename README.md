# docetl-examples

This repository contains examples of DocETL pipelines. Currently, it includes:

## ICLR 2024 Review Analysis

Analyzes reviews from ICLR 2024 conference submissions to identify common themes in reviewer feedback, particularly focusing on strengths and weaknesses mentioned across papers.

### Data

The review data is stored using Git LFS (Large File Storage) due to its size. To work with the data:

1. Install Git LFS if you haven't already:

```bash
brew install git-lfs
git lfs install
```

2. Clone the repository with LFS support:

```bash
git clone https://github.com/ucbepic/docetl-examples.git
```

3. Pull the large files:

```bash
git lfs pull
```
