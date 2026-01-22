process REPORT_STATS {
    tag "${meta.id}"
    label 'process_single'

    conda "conda-forge::pandas=1.4.3"
    container "${workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container
        ? 'https://depot.galaxyproject.org/singularity/pandas:1.4.3'
        : 'biocontainers/pandas:1.4.3'}"

    input:
    //path bed
    tuple val(meta), path(flagstat), path(mosdepth_summary)

    output:
    tuple val(meta), path("*.tsv"), emit: summary
    path "versions.yml", emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def prefix = task.ext.prefix ?: "${meta.id}"

    """
    chromosome_coverage_depth_summary.py \\
        --samtools_flagstat ${flagstat} \\
        --mosdepth_summary ${mosdepth_summary} \\
        --sample ${prefix} \\
        --output ${prefix}.chromosome_coverage_depth_summary.tsv

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version | sed 's/Python //g')
    END_VERSIONS
    """
}
