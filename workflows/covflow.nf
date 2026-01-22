/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT MODULES / SUBWORKFLOWS / FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
include { paramsSummaryMap } from 'plugin/nf-schema'
include { paramsSummaryMultiqc } from '../subworkflows/nf-core/utils_nfcore_pipeline'
include { softwareVersionsToYAML } from '../subworkflows/nf-core/utils_nfcore_pipeline'
include { methodsDescriptionText } from '../subworkflows/local/utils_nfcore_covflow_pipeline'
include { COLLAPSE_PRIMERS } from '../modules/local/collapse_primers'
include { MOSDEPTH as MOSDEPTH_GENOME } from '../modules/local/mosdepth/main'
include { MOSDEPTH as MOSDEPTH_AMPLICON } from '../modules/local/mosdepth/main'
include { REPORT_PLOT_REGIONS as REPORT_PLOT_REGIONS_GENOME } from '../modules/local/report/plot/regions'
include { REPORT_PLOT_REGIONS as REPORT_PLOT_REGIONS_AMPLICON } from '../modules/local/report/plot/regions'
include { SAMTOOLS_INDEX } from '../modules/nf-core/samtools/index/main'
include { BAM_SORT_STATS_SAMTOOLS } from '../subworkflows/nf-core/bam_sort_stats_samtools/main'
include { BAM_STATS_SAMTOOLS } from '../subworkflows/nf-core/bam_stats_samtools/main'
include { REPORT_STATS } from '../modules/local/report/stats/main'
include { SAMTOOLS_COVERAGE } from '../modules/nf-core/samtools/coverage/main'
include { SAMTOOLS_FAIDX } from '../modules/nf-core/samtools/faidx/main'
include { CSVTK_CONCAT } from '../modules/local/csvtk/concat/main.nf'

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RUN MAIN WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow COVFLOW {
    take:
    ch_sample // channel: samplesheet read in from --input [meta, [bam, ref, primer_bed]]

    main:

    ch_versions = channel.empty()

    ch_sample.map{
        meta, data ->
            def it = data
            def bam = it[0]
            def ref = it[1]
            def bed = it[2]
            [meta, ref]
        }.set {
            ch_ref
    }
    //ch_ref.view()
    SAMTOOLS_FAIDX(ch_ref, [[],[]], false)
    ch_versions = ch_versions.mix(SAMTOOLS_FAIDX.out.versions)
    ch_fai = SAMTOOLS_FAIDX.out.fai
    //ch_fai.view()

    //ch_sample.join(ch_fai).view()

    ch_sample.join(ch_fai)
        .multiMap { _meta, _data, _fai ->
            def meta = _meta
            def it = _data
            def bam = it[0]
            def ref = it[1]
            def bed = it[2]
            def fai = _fai
            bam: [meta, bam]
            bam_bed: [meta, bam, bed]
            primer_bed: [meta, bed]
            ref: [meta, ref]
            ref_fai: [meta, ref, fai]
            fai: [meta, fai]
        }
        .set {
            ch_input
        }
    //ch_input.bam.view()
    //ch_input.ref.view()

    ch_versions = ch_versions.mix(SAMTOOLS_FAIDX.out.versions)

    BAM_SORT_STATS_SAMTOOLS(ch_input.bam, ch_input.ref)
    ch_versions = ch_versions.mix(BAM_SORT_STATS_SAMTOOLS.out.versions)

    ch_bam_bai = BAM_SORT_STATS_SAMTOOLS.out.bam.join(BAM_SORT_STATS_SAMTOOLS.out.bai)
    ch_bam_bai.join(ch_input.ref_fai)
        .multiMap { meta, bam, bai, ref, fai ->
            bam_bai: [meta, bam, bai]
            ref: [meta, ref]
            fai: [meta, fai]
        }
        .set {
            ch_input_to_coverage
        }
    SAMTOOLS_COVERAGE(ch_input_to_coverage.bam_bai, ch_input_to_coverage.ref, ch_input_to_coverage.fai)
    ch_versions = ch_versions.mix(SAMTOOLS_COVERAGE.out.versions)


    ch_bam_bai
        .join(ch_input.ref)
        .multiMap { meta, bam, bai, ref ->
            bam_bai_bed: [meta, bam, bai, []]
            ref: [meta, ref]
        }
        .set {
            ch_input_genome_depth
        }
    //ch_input_genome_depth.bam_bai_bed.view()
    MOSDEPTH_GENOME(ch_input_genome_depth.bam_bai_bed, ch_input_genome_depth.ref)

    ch_versions = ch_versions.mix(MOSDEPTH_GENOME.out.versions.first().ifEmpty(null))

    REPORT_STATS(
        BAM_SORT_STATS_SAMTOOLS.out.flagstat
            //.join(MOSDEPTH_GENOME.out.thresholds_bed)
            .join(MOSDEPTH_GENOME.out.summary_txt)
    )
    CSVTK_CONCAT(
        REPORT_STATS.out.summary
        .map { it -> it[1] }.collect()
        .map { files -> tuple([id: "chromosome_coverage_depth_summary"], files) },
        'tsv',
        'tsv',
    )
    REPORT_PLOT_REGIONS_GENOME(
        MOSDEPTH_GENOME.out.regions_bed.collect { it[1] }
    )
    ch_versions = ch_versions.mix(REPORT_PLOT_REGIONS_GENOME.out.versions)

    // for amplicon
    //ch_input.primer_bed.view()
    COLLAPSE_PRIMERS(ch_input.primer_bed, params.primer_left_suffix, params.primer_right_suffix)
    ch_primer_collapsed_bed = COLLAPSE_PRIMERS.out.bed
    ch_versions = ch_versions.mix(COLLAPSE_PRIMERS.out.versions)

    ch_bam_bai_bed = ch_bam_bai.combine(ch_primer_collapsed_bed)
    ch_bam_bai_bed
        .join(ch_input.ref)
        .multiMap { meta, bam, bai, bed, ref ->
            bam_bai_bed: [meta, bam, bai, bed]
            ref: [meta, ref]
        }
        .set {
            ch_input_amp_depth
        }

    MOSDEPTH_AMPLICON(ch_input_amp_depth.bam_bai_bed, ch_input_amp_depth.ref)

    ch_versions = ch_versions.mix(MOSDEPTH_AMPLICON.out.versions.first().ifEmpty(null))
    REPORT_PLOT_REGIONS_AMPLICON(
        MOSDEPTH_AMPLICON.out.regions_bed.collect { it[1] }
    )
    ch_versions = ch_versions.mix(REPORT_PLOT_REGIONS_AMPLICON.out.versions)
    //
    // Collate and save software versions
    //
    softwareVersionsToYAML(ch_versions)
        .collectFile(
            storeDir: "${params.outdir}/pipeline_info",
            name: 'software_versions.yml',
            sort: true,
            newLine: true,
        )



    emit:

    versions = ch_versions // channel: [ path(versions.yml) ]
}
