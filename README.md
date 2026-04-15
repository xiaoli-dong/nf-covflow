# nf-covflow
A lightweight Nextflow pipeline for calculating genome coverage and depth profiles from aligned sequencing data (BAM), with optional region-based analysis and visualization. nf-covflow is designed to compute:

- 📊 Genome-wide coverage statistics
- 📈 Per-base depth profiles
- 🧾 Region-specific coverage using BED files
- 📉 Coverage and depth plots

The pipeline is simple, fast, and suitable for viral genomics QC or general alignment-based coverage assessment.

---

## Quick Start
> [!NOTE]
> If you are new to Nextflow and nf-core, please refer to [this page](https://nf-co.re/docs/usage/installation) on how to set up Nextflow. Make sure to [test your setup](https://nf-co.re/docs/usage/introduction#how-to-run-a-pipeline) with `-profile test` before running the workflow on actual data.

### Check Workflow Options

Please clone nf-qcflow from gitHub to your local computer. To check the pipeline command-line options:

```bash
nextflow run path_to/nf-covflow/main --help
```
### Prepare Required Samplesheet Input

The nf-covflow pipeline requires a CSV format samplesheet containing the path to bam mapping file, reference file when generating bam file, and the primer scheme bed file. See below for what the samplesheet looks like:

**samplesheet.csv**

```csv
sample,bam,ref_fasta,bed_file
barcode49,path_to/barcode49.sorted.bam,path_to/reference.fasta,path_to/scheme.bed
barcode50,path_to/barcode50.sorted.bam,path_to/reference.fasta,path_to/scheme.bed
```

### Run the pipeline
Now you can run the pipeline using 
```
# run on the cluster with slurm
nextflow run "${path_to/nf-covflow}/main.nf" \
   -profile singularity,slurm \
   --input path_to/samplesheet.csv \
   --outdir results \
   -resume

# run without slurm
nextflow run "${path_to/nf-covflow}/main.nf" \
   -profile singularity \
   --input path_to/samplesheet.csv \
   --outdir results \
   -resume
```


