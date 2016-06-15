.. _examples:

========
Examples
========

Bioinformatics
==============

ATAC-seq pipeline
-----------------

This sample script does some basic processing of the data from the original ATAC-seq paper
(https://dx.doi.org/10.1038/nmeth.2688). First, the sequence data is cleaned up by removing adapter sequence, then it's aligned to
the reference genome with bwa, then a subset of the alignments are selected for peak calling, which is done with macs2.

Note the `drmr:label` and `drmr:job` directives. Often when you're developing a pipeline, you need to correct it and run it again.
Maybe you didn't specify enough memory for a job and it was killed by the resource manager, stopping the entire pipeline, or you
want to tweak some program arguments and rerun just that step. You can do that with drmr's ``--from-label`` and ``--to-label``
options. ::

    #!/bin/bash
    # -*- mode: sh; coding: utf-8 -*-

    #
    # trim adapter sequence from reads
    #

    # drmr:label trim-adapters
    # drmr:job time_limit=4h working_directory=/drmr/example/atac-seq

    /usr/bin/time -v ionice -c3 cta SRR891268_1.fq.gz SRR891268_2.fq.gz
    /usr/bin/time -v ionice -c3 cta SRR891269_1.fq.gz SRR891269_2.fq.gz
    /usr/bin/time -v ionice -c3 cta SRR891270_1.fq.gz SRR891270_2.fq.gz
    /usr/bin/time -v ionice -c3 cta SRR891271_1.fq.gz SRR891271_2.fq.gz
    /usr/bin/time -v ionice -c3 cta SRR891272_1.fq.gz SRR891272_2.fq.gz
    /usr/bin/time -v ionice -c3 cta SRR891273_1.fq.gz SRR891273_2.fq.gz
    /usr/bin/time -v ionice -c3 cta SRR891274_1.fq.gz SRR891274_2.fq.gz
    /usr/bin/time -v ionice -c3 cta SRR891275_1.fq.gz SRR891275_2.fq.gz
    /usr/bin/time -v ionice -c3 cta SRR891276_1.fq.gz SRR891276_2.fq.gz
    /usr/bin/time -v ionice -c3 cta SRR891277_1.fq.gz SRR891277_2.fq.gz
    /usr/bin/time -v ionice -c3 cta SRR891278_1.fq.gz SRR891278_2.fq.gz
    /usr/bin/time -v ionice -c3 cta SRR891279_1.fq.gz SRR891279_2.fq.gz
    /usr/bin/time -v ionice -c3 cta SRR891280_1.fq.gz SRR891280_2.fq.gz

    # drmr:wait

    #
    # align the reads to the hg19 reference genome
    #

    # drmr:label bwa
    # drmr:job nodes=1 processors=4 working_directory=/drmr/example/atac-seq

    /usr/bin/time -v ionice -c3 bwa mem -t 4 /lab/data/reference/human/hg19/index/bwa/0.7.12/hg19 SRR891268_1.trimmed.fq.gz SRR891268_2.trimmed.fq.gz | samtools sort -m 1g -@ 4 -O bam -T SRR891268.sort -o SRR891268.bam -
    /usr/bin/time -v ionice -c3 bwa mem -t 4 /lab/data/reference/human/hg19/index/bwa/0.7.12/hg19 SRR891269_1.trimmed.fq.gz SRR891269_2.trimmed.fq.gz | samtools sort -m 1g -@ 4 -O bam -T SRR891269.sort -o SRR891269.bam -
    /usr/bin/time -v ionice -c3 bwa mem -t 4 /lab/data/reference/human/hg19/index/bwa/0.7.12/hg19 SRR891270_1.trimmed.fq.gz SRR891270_2.trimmed.fq.gz | samtools sort -m 1g -@ 4 -O bam -T SRR891270.sort -o SRR891270.bam -
    /usr/bin/time -v ionice -c3 bwa mem -t 4 /lab/data/reference/human/hg19/index/bwa/0.7.12/hg19 SRR891271_1.trimmed.fq.gz SRR891271_2.trimmed.fq.gz | samtools sort -m 1g -@ 4 -O bam -T SRR891271.sort -o SRR891271.bam -
    /usr/bin/time -v ionice -c3 bwa mem -t 4 /lab/data/reference/human/hg19/index/bwa/0.7.12/hg19 SRR891272_1.trimmed.fq.gz SRR891272_2.trimmed.fq.gz | samtools sort -m 1g -@ 4 -O bam -T SRR891272.sort -o SRR891272.bam -
    /usr/bin/time -v ionice -c3 bwa mem -t 4 /lab/data/reference/human/hg19/index/bwa/0.7.12/hg19 SRR891273_1.trimmed.fq.gz SRR891273_2.trimmed.fq.gz | samtools sort -m 1g -@ 4 -O bam -T SRR891273.sort -o SRR891273.bam -
    /usr/bin/time -v ionice -c3 bwa mem -t 4 /lab/data/reference/human/hg19/index/bwa/0.7.12/hg19 SRR891274_1.trimmed.fq.gz SRR891274_2.trimmed.fq.gz | samtools sort -m 1g -@ 4 -O bam -T SRR891274.sort -o SRR891274.bam -
    /usr/bin/time -v ionice -c3 bwa mem -t 4 /lab/data/reference/human/hg19/index/bwa/0.7.12/hg19 SRR891275_1.trimmed.fq.gz SRR891275_2.trimmed.fq.gz | samtools sort -m 1g -@ 4 -O bam -T SRR891275.sort -o SRR891275.bam -
    /usr/bin/time -v ionice -c3 bwa mem -t 4 /lab/data/reference/human/hg19/index/bwa/0.7.12/hg19 SRR891276_1.trimmed.fq.gz SRR891276_2.trimmed.fq.gz | samtools sort -m 1g -@ 4 -O bam -T SRR891276.sort -o SRR891276.bam -
    /usr/bin/time -v ionice -c3 bwa mem -t 4 /lab/data/reference/human/hg19/index/bwa/0.7.12/hg19 SRR891277_1.trimmed.fq.gz SRR891277_2.trimmed.fq.gz | samtools sort -m 1g -@ 4 -O bam -T SRR891277.sort -o SRR891277.bam -
    /usr/bin/time -v ionice -c3 bwa mem -t 4 /lab/data/reference/human/hg19/index/bwa/0.7.12/hg19 SRR891278_1.trimmed.fq.gz SRR891278_2.trimmed.fq.gz | samtools sort -m 1g -@ 4 -O bam -T SRR891278.sort -o SRR891278.bam -
    /usr/bin/time -v ionice -c3 bwa mem -t 4 /lab/data/reference/human/hg19/index/bwa/0.7.12/hg19 SRR891279_1.trimmed.fq.gz SRR891279_2.trimmed.fq.gz | samtools sort -m 1g -@ 4 -O bam -T SRR891279.sort -o SRR891279.bam -
    /usr/bin/time -v ionice -c3 bwa mem -t 4 /lab/data/reference/human/hg19/index/bwa/0.7.12/hg19 SRR891280_1.trimmed.fq.gz SRR891280_2.trimmed.fq.gz | samtools sort -m 1g -@ 4 -O bam -T SRR891280.sort -o SRR891280.bam -

    # drmr:wait

    # drmr:label mark-duplicates
    # drmr:job nodes=1 processors=2 memory=9g working_directory=/drmr/example/atac-seq

    /usr/bin/time -v java -Xmx8g -jar $PICARD_HOME/picard.jar MarkDuplicates I=SRR891268.bam O=SRR891268.md.bam ASSUME_SORTED=true METRICS_FILE=SRR891268.markdup.metrics VALIDATION_STRINGENCY=LENIENT TMP_DIR=/drmr/example/atac-seq
    /usr/bin/time -v java -Xmx8g -jar $PICARD_HOME/picard.jar MarkDuplicates I=SRR891269.bam O=SRR891269.md.bam ASSUME_SORTED=true METRICS_FILE=SRR891269.markdup.metrics VALIDATION_STRINGENCY=LENIENT TMP_DIR=/drmr/example/atac-seq
    /usr/bin/time -v java -Xmx8g -jar $PICARD_HOME/picard.jar MarkDuplicates I=SRR891270.bam O=SRR891270.md.bam ASSUME_SORTED=true METRICS_FILE=SRR891270.markdup.metrics VALIDATION_STRINGENCY=LENIENT TMP_DIR=/drmr/example/atac-seq
    /usr/bin/time -v java -Xmx8g -jar $PICARD_HOME/picard.jar MarkDuplicates I=SRR891271.bam O=SRR891271.md.bam ASSUME_SORTED=true METRICS_FILE=SRR891271.markdup.metrics VALIDATION_STRINGENCY=LENIENT TMP_DIR=/drmr/example/atac-seq
    /usr/bin/time -v java -Xmx8g -jar $PICARD_HOME/picard.jar MarkDuplicates I=SRR891272.bam O=SRR891272.md.bam ASSUME_SORTED=true METRICS_FILE=SRR891272.markdup.metrics VALIDATION_STRINGENCY=LENIENT TMP_DIR=/drmr/example/atac-seq
    /usr/bin/time -v java -Xmx8g -jar $PICARD_HOME/picard.jar MarkDuplicates I=SRR891273.bam O=SRR891273.md.bam ASSUME_SORTED=true METRICS_FILE=SRR891273.markdup.metrics VALIDATION_STRINGENCY=LENIENT TMP_DIR=/drmr/example/atac-seq
    /usr/bin/time -v java -Xmx8g -jar $PICARD_HOME/picard.jar MarkDuplicates I=SRR891274.bam O=SRR891274.md.bam ASSUME_SORTED=true METRICS_FILE=SRR891274.markdup.metrics VALIDATION_STRINGENCY=LENIENT TMP_DIR=/drmr/example/atac-seq
    /usr/bin/time -v java -Xmx8g -jar $PICARD_HOME/picard.jar MarkDuplicates I=SRR891275.bam O=SRR891275.md.bam ASSUME_SORTED=true METRICS_FILE=SRR891275.markdup.metrics VALIDATION_STRINGENCY=LENIENT TMP_DIR=/drmr/example/atac-seq
    /usr/bin/time -v java -Xmx8g -jar $PICARD_HOME/picard.jar MarkDuplicates I=SRR891276.bam O=SRR891276.md.bam ASSUME_SORTED=true METRICS_FILE=SRR891276.markdup.metrics VALIDATION_STRINGENCY=LENIENT TMP_DIR=/drmr/example/atac-seq
    /usr/bin/time -v java -Xmx8g -jar $PICARD_HOME/picard.jar MarkDuplicates I=SRR891277.bam O=SRR891277.md.bam ASSUME_SORTED=true METRICS_FILE=SRR891277.markdup.metrics VALIDATION_STRINGENCY=LENIENT TMP_DIR=/drmr/example/atac-seq
    /usr/bin/time -v java -Xmx8g -jar $PICARD_HOME/picard.jar MarkDuplicates I=SRR891278.bam O=SRR891278.md.bam ASSUME_SORTED=true METRICS_FILE=SRR891278.markdup.metrics VALIDATION_STRINGENCY=LENIENT TMP_DIR=/drmr/example/atac-seq
    /usr/bin/time -v java -Xmx8g -jar $PICARD_HOME/picard.jar MarkDuplicates I=SRR891279.bam O=SRR891279.md.bam ASSUME_SORTED=true METRICS_FILE=SRR891279.markdup.metrics VALIDATION_STRINGENCY=LENIENT TMP_DIR=/drmr/example/atac-seq
    /usr/bin/time -v java -Xmx8g -jar $PICARD_HOME/picard.jar MarkDuplicates I=SRR891280.bam O=SRR891280.md.bam ASSUME_SORTED=true METRICS_FILE=SRR891280.markdup.metrics VALIDATION_STRINGENCY=LENIENT TMP_DIR=/drmr/example/atac-seq

    # drmr:wait

    #
    # index the merged BAM files with marked duplicates, so we can prune them
    #

    # drmr:label index-sample-libraries

    /usr/bin/time -v samtools index SRR891268.md.bam
    /usr/bin/time -v samtools index SRR891269.md.bam
    /usr/bin/time -v samtools index SRR891270.md.bam
    /usr/bin/time -v samtools index SRR891271.md.bam
    /usr/bin/time -v samtools index SRR891272.md.bam
    /usr/bin/time -v samtools index SRR891273.md.bam
    /usr/bin/time -v samtools index SRR891274.md.bam
    /usr/bin/time -v samtools index SRR891275.md.bam
    /usr/bin/time -v samtools index SRR891276.md.bam
    /usr/bin/time -v samtools index SRR891277.md.bam
    /usr/bin/time -v samtools index SRR891278.md.bam
    /usr/bin/time -v samtools index SRR891279.md.bam
    /usr/bin/time -v samtools index SRR891280.md.bam

    # drmr:wait

    #
    # prune the BAM files with marked duplicates down to properly paired
    # and mapped primary autosomal alignments of good quality, for peak calling
    #

    # drmr:label prune
    # drmr:job nodes=1 processors=1 memory=4g time_limit=4h working_directory=/drmr/example/atac-seq

    /usr/bin/time -v bash -c "(export CHROMOSOMES=$(samtools view -H SRR891268.md.bam | grep '^@SQ' | cut -f 2 | grep -v -e _ -e chrM -e chrX -e chrY -e 'VN:' | sed 's/SN://' | xargs echo); samtools view -b -h -f 3 -F 4 -F 8 -F 256 -F 1024 -F 2048 -q 30 SRR891268.md.bam $CHROMOSOMES > SRR891268.pruned.bam)"
    /usr/bin/time -v bash -c "(export CHROMOSOMES=$(samtools view -H SRR891269.md.bam | grep '^@SQ' | cut -f 2 | grep -v -e _ -e chrM -e chrX -e chrY -e 'VN:' | sed 's/SN://' | xargs echo); samtools view -b -h -f 3 -F 4 -F 8 -F 256 -F 1024 -F 2048 -q 30 SRR891269.md.bam $CHROMOSOMES > SRR891269.pruned.bam)"
    /usr/bin/time -v bash -c "(export CHROMOSOMES=$(samtools view -H SRR891270.md.bam | grep '^@SQ' | cut -f 2 | grep -v -e _ -e chrM -e chrX -e chrY -e 'VN:' | sed 's/SN://' | xargs echo); samtools view -b -h -f 3 -F 4 -F 8 -F 256 -F 1024 -F 2048 -q 30 SRR891270.md.bam $CHROMOSOMES > SRR891270.pruned.bam)"
    /usr/bin/time -v bash -c "(export CHROMOSOMES=$(samtools view -H SRR891271.md.bam | grep '^@SQ' | cut -f 2 | grep -v -e _ -e chrM -e chrX -e chrY -e 'VN:' | sed 's/SN://' | xargs echo); samtools view -b -h -f 3 -F 4 -F 8 -F 256 -F 1024 -F 2048 -q 30 SRR891271.md.bam $CHROMOSOMES > SRR891271.pruned.bam)"
    /usr/bin/time -v bash -c "(export CHROMOSOMES=$(samtools view -H SRR891272.md.bam | grep '^@SQ' | cut -f 2 | grep -v -e _ -e chrM -e chrX -e chrY -e 'VN:' | sed 's/SN://' | xargs echo); samtools view -b -h -f 3 -F 4 -F 8 -F 256 -F 1024 -F 2048 -q 30 SRR891272.md.bam $CHROMOSOMES > SRR891272.pruned.bam)"
    /usr/bin/time -v bash -c "(export CHROMOSOMES=$(samtools view -H SRR891273.md.bam | grep '^@SQ' | cut -f 2 | grep -v -e _ -e chrM -e chrX -e chrY -e 'VN:' | sed 's/SN://' | xargs echo); samtools view -b -h -f 3 -F 4 -F 8 -F 256 -F 1024 -F 2048 -q 30 SRR891273.md.bam $CHROMOSOMES > SRR891273.pruned.bam)"
    /usr/bin/time -v bash -c "(export CHROMOSOMES=$(samtools view -H SRR891274.md.bam | grep '^@SQ' | cut -f 2 | grep -v -e _ -e chrM -e chrX -e chrY -e 'VN:' | sed 's/SN://' | xargs echo); samtools view -b -h -f 3 -F 4 -F 8 -F 256 -F 1024 -F 2048 -q 30 SRR891274.md.bam $CHROMOSOMES > SRR891274.pruned.bam)"
    /usr/bin/time -v bash -c "(export CHROMOSOMES=$(samtools view -H SRR891275.md.bam | grep '^@SQ' | cut -f 2 | grep -v -e _ -e chrM -e chrX -e chrY -e 'VN:' | sed 's/SN://' | xargs echo); samtools view -b -h -f 3 -F 4 -F 8 -F 256 -F 1024 -F 2048 -q 30 SRR891275.md.bam $CHROMOSOMES > SRR891275.pruned.bam)"
    /usr/bin/time -v bash -c "(export CHROMOSOMES=$(samtools view -H SRR891276.md.bam | grep '^@SQ' | cut -f 2 | grep -v -e _ -e chrM -e chrX -e chrY -e 'VN:' | sed 's/SN://' | xargs echo); samtools view -b -h -f 3 -F 4 -F 8 -F 256 -F 1024 -F 2048 -q 30 SRR891276.md.bam $CHROMOSOMES > SRR891276.pruned.bam)"
    /usr/bin/time -v bash -c "(export CHROMOSOMES=$(samtools view -H SRR891277.md.bam | grep '^@SQ' | cut -f 2 | grep -v -e _ -e chrM -e chrX -e chrY -e 'VN:' | sed 's/SN://' | xargs echo); samtools view -b -h -f 3 -F 4 -F 8 -F 256 -F 1024 -F 2048 -q 30 SRR891277.md.bam $CHROMOSOMES > SRR891277.pruned.bam)"
    /usr/bin/time -v bash -c "(export CHROMOSOMES=$(samtools view -H SRR891278.md.bam | grep '^@SQ' | cut -f 2 | grep -v -e _ -e chrM -e chrX -e chrY -e 'VN:' | sed 's/SN://' | xargs echo); samtools view -b -h -f 3 -F 4 -F 8 -F 256 -F 1024 -F 2048 -q 30 SRR891278.md.bam $CHROMOSOMES > SRR891278.pruned.bam)"
    /usr/bin/time -v bash -c "(export CHROMOSOMES=$(samtools view -H SRR891279.md.bam | grep '^@SQ' | cut -f 2 | grep -v -e _ -e chrM -e chrX -e chrY -e 'VN:' | sed 's/SN://' | xargs echo); samtools view -b -h -f 3 -F 4 -F 8 -F 256 -F 1024 -F 2048 -q 30 SRR891279.md.bam $CHROMOSOMES > SRR891279.pruned.bam)"
    /usr/bin/time -v bash -c "(export CHROMOSOMES=$(samtools view -H SRR891280.md.bam | grep '^@SQ' | cut -f 2 | grep -v -e _ -e chrM -e chrX -e chrY -e 'VN:' | sed 's/SN://' | xargs echo); samtools view -b -h -f 3 -F 4 -F 8 -F 256 -F 1024 -F 2048 -q 30 SRR891280.md.bam $CHROMOSOMES > SRR891280.pruned.bam)"

    # drmr:wait

    #
    # peak calling
    #

    # drmr:label macs2
    # drmr:job nodes=1 processors=1 memory=8g working_directory=/drmr/example/atac-seq

    /usr/bin/time -v ionice -c3 macs2 callpeak -t SRR891268.pruned.bam -f BAM -n SRR891268.broad -g hs --nomodel --shift -100 --extsize 200 -B --broad --keep-dup all
    /usr/bin/time -v ionice -c3 macs2 callpeak -t SRR891269.pruned.bam -f BAM -n SRR891269.broad -g hs --nomodel --shift -100 --extsize 200 -B --broad --keep-dup all
    /usr/bin/time -v ionice -c3 macs2 callpeak -t SRR891270.pruned.bam -f BAM -n SRR891270.broad -g hs --nomodel --shift -100 --extsize 200 -B --broad --keep-dup all
    /usr/bin/time -v ionice -c3 macs2 callpeak -t SRR891271.pruned.bam -f BAM -n SRR891271.broad -g hs --nomodel --shift -100 --extsize 200 -B --broad --keep-dup all
    /usr/bin/time -v ionice -c3 macs2 callpeak -t SRR891272.pruned.bam -f BAM -n SRR891272.broad -g hs --nomodel --shift -100 --extsize 200 -B --broad --keep-dup all
    /usr/bin/time -v ionice -c3 macs2 callpeak -t SRR891273.pruned.bam -f BAM -n SRR891273.broad -g hs --nomodel --shift -100 --extsize 200 -B --broad --keep-dup all
    /usr/bin/time -v ionice -c3 macs2 callpeak -t SRR891274.pruned.bam -f BAM -n SRR891274.broad -g hs --nomodel --shift -100 --extsize 200 -B --broad --keep-dup all
    /usr/bin/time -v ionice -c3 macs2 callpeak -t SRR891275.pruned.bam -f BAM -n SRR891275.broad -g hs --nomodel --shift -100 --extsize 200 -B --broad --keep-dup all
    /usr/bin/time -v ionice -c3 macs2 callpeak -t SRR891276.pruned.bam -f BAM -n SRR891276.broad -g hs --nomodel --shift -100 --extsize 200 -B --broad --keep-dup all
    /usr/bin/time -v ionice -c3 macs2 callpeak -t SRR891277.pruned.bam -f BAM -n SRR891277.broad -g hs --nomodel --shift -100 --extsize 200 -B --broad --keep-dup all
    /usr/bin/time -v ionice -c3 macs2 callpeak -t SRR891278.pruned.bam -f BAM -n SRR891278.broad -g hs --nomodel --shift -100 --extsize 200 -B --broad --keep-dup all
    /usr/bin/time -v ionice -c3 macs2 callpeak -t SRR891279.pruned.bam -f BAM -n SRR891279.broad -g hs --nomodel --shift -100 --extsize 200 -B --broad --keep-dup all
    /usr/bin/time -v ionice -c3 macs2 callpeak -t SRR891280.pruned.bam -f BAM -n SRR891280.broad -g hs --nomodel --shift -100 --extsize 200 -B --broad --keep-dup all
