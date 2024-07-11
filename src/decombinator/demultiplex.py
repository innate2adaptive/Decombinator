# Demultiplexor
# James M. Heather, August 2016, UCL
# https://innate2adaptive.github.io/Decombinator/

##################
### BACKGROUND ###
##################

# Version 4.2 takes  three (single index or old internal index protocol) or four (DUI) reads and demultiplexes


# A derivate of DualIndexDemultiplexing.py/FuzzyDID, fuzzily demultiplexes ligation TCR sequencing protocol FASTQ data
# i.e. allows a specified number of mismatches in the index sequence

##################
###### INPUT #####
##################

# Requires the command line input of  3 or 4 file names, giving the two Illumina sequence reads, plus the one or two index reads.
# Files may be uncompressed, or gzipped (and be named accordingly, e.g. File.fastq.gz)
# A additonal optional comma delimited file detailing sample index specifics is strongly recommended, allowing
# production of correctly named files
# File must give the following details, one sample (or index combination) per line, with no empty lines:
# Sample name, SP1/R1 index (I), SP2/R2 index (L):
# e.g.: AlphaSample,1,11
# If you include one and only one chain description (i.e. alpha, beta, gamma or delta) into your sample name, you need not set chain in Decombinator

# e.g. run: python Demultiplexor.py -r1 read1.fastq -r2 read2.fastq -i1 indexread1.fastq indexread2.fastq -ix indexes.ndx

# NOTE V4.2 simply takes the two Illumina sequence reads, demultiplexes and outputs two reads per sample (annotated _R1, and _R2)
# plus two undetermined reads.  In contrast to earlier versions, note that Demultiplexor does not attach a barcode from
# read 2 to read 1. This is done direcly in Decombinator.

# Other optional flags:

# -s/--supresssummary: Suppress the production of a summary file containing details of the run into a 'Logs' directory.

# -a/--outputall: Output the results of all possible index combinations currently used in protocol
# e.g. Useful in finding potential cross-contaminating or incorrectly indexed samples
# NB - This option can be run even if an index list is provided (although only those provided by the index list will be named)

# -t/--threshold: Specifies the threshold by which indexes can be clustered by fuzzy string matching, allowing for sequencing errors
# Default = 2. Setting to zero turns off fuzzy matching, i.e. only allowing exact string matching

# -dz/--dontgzip: Suppress the automatic compression of output demultiplexed FASTQ files with gzip.
# Using this flag makes the script execute faster, but data will require more storage space.

# -dc/--dontcount: Suppress whether or not to show the running line count, every 100,000 reads.
# Helps in monitoring progress of large batches.

# -fz/--fuzzylist: Output a list of FASTQ IDs of reads which are demultiplexed using fuzzy (i.e. non-exact) index matching, within the specified threshold.
# Default = False, but can be useful to investigate suspected cases of poor quality index reads or clashing sequences.

# -ex/--extension: Allows users to specify the file extension of the demultiplexed FASTQ files produced.

# -cl/--compresslevel: Allows user to specify the speed of gzip compression of output files as an integer from 1 to 9.
# 1 is the fastest but offers least compression, 9 is the slowest and offers the most compression. Default for this program is 4.

# To see all options, run: python Demultiplexor.py -h


##################
##### OUTPUT #####
##################

# Versions up to 4.2.
# A fastq file will be produced for each sample listed in the index file, in the modified format, containing all reads that matched
# So we go from:        R1 - [6s|X1|----J(D)V-----]
#                       R2 - [X2]
#                       R3 - [8s|N1|8s|N2|2s|-----5'UTR-----]
# To: ========>         out- [8s|N1|8s|N2|2s|X1|X2|----J(D)V-----]
# Where X = hexamer index sequence, N = random barcode sequence, and Ys = spacer sequences of length Y
# The 8s sequences can be used downstream to identify the presence and location of random barcode N sequences
# 2s is also kept to allow for the possibility finding N sequences produced from slipped reads

# Version 4.2 Produces 2 outputs per paired index, which are simply R1 and R2 Illumina reads.
# NOTE No barcode manipulation is carried out any longer

################
#### PACKAGES ####
##################

from __future__ import division
import time
import sys
import argparse
import gzip
import os
import itertools
import Levenshtein as lev
import collections as coll
from Bio.Seq import Seq
from importlib import metadata

##########################################################
############# READ IN COMMAND LINE ARGUMENTS #############
##########################################################


def args():
    """args(): Obtains command line arguments which dictate the script's behaviour"""

    # Help flag
    parser = argparse.ArgumentParser(
        description="Script to demultiplex FASTQ data produced using the Chain labs' ligation TCRseq protocol. Please see https://innate2adaptive.github.io/Decombinator/ for details."
    )
    # Add arguments
    parser.add_argument(
        "-r1", "--read1", type=str, help="Read 1 FASTQ file", required=True
    )
    parser.add_argument(
        "-r2", "--read2", type=str, help="Read 2 FASTQ file", required=True
    )
    parser.add_argument(
        "-i1", "--index1", type=str, help="Index read FASTQ file", required=True
    )
    parser.add_argument(
        "-i2",
        "--index2",
        type=str,
        help="Second index read FASTQ file (if dual indexing)",
        required=False,
    )
    parser.add_argument(
        "-ix",
        "--indexlist",
        type=str,
        help="File containing sample/index table",
        required=False,
    )
    parser.add_argument(
        "-t",
        "--threshold",
        type=int,
        help="Edit distance allowed for fuzzy-string index matching (default=2)",
        required=False,
        default=2,
    )
    parser.add_argument(
        "-s",
        "--suppresssummary",
        action="store_true",
        help="Output summary data",
        required=False,
    )
    parser.add_argument(
        "-a",
        "--outputall",
        action="store_true",
        help="Output all possible index combinations",
        required=False,
    )
    parser.add_argument(
        "-dz",
        "--dontgzip",
        action="store_true",
        help="Stop the output FASTQ files automatically being compressed with gzip (True/False)",
        required=False,
    )
    parser.add_argument(
        "-dc",
        "--dontcount",
        action="store_true",
        help="Show the count (True/False)",
        required=False,
    )
    parser.add_argument(
        "-fl",
        "--fuzzylist",
        type=bool,
        help="Output a list of those reads that demultiplexed using fuzzy index matching (True/False)",
        required=False,
        default=False,
    )
    parser.add_argument(
        "-ex",
        "--extension",
        type=str,
        help='Specify the file extension of the output FASTQ files. Default = "fq"',
        required=False,
        default="fq",
    )
    parser.add_argument(
        "-cl",
        "--compresslevel",
        type=int,
        choices=range(1, 10),
        help="Specify compression level for output files",
        required=False,
        default=4,
    )
    return parser.parse_args()


############################################
############# FASTQ PROCESSING #############
############################################


def fastq_check(infile):
    """fastq_check(file): Performs a rudimentary sanity check to see whether a file is indeed a FASTQ file"""

    success = True

    if infile.endswith(".gz"):
        # print("TEST1")
        with gzip.open(infile, "rt") as possfq:
            read = [i for i in itertools.islice(possfq, 0, 4)]
    else:
        with open(infile) as possfq:
            read = [i for i in itertools.islice(possfq, 0, 4)]

    # @ check
    if not read[0][0] == "@":

        success = False
    # Descriptor check
    if not read[2][0] == "+":

        success = False
    # Read/quality match check
    if not len(read[1]) == len(read[3]):
        print(len(read[1]), len(read[3]))
        success = False

    return success


def readfq(fp):
    """readfq(file):Heng Li's Python implementation of his readfq function
    See https://github.com/lh3/readfq/blob/master/readfq.py"""

    last = None  # this is a buffer keeping the last unprocessed line
    while True:  # mimic closure; is it a bad idea?
        if not last:  # the first record or a record following a fastq
            for l in fp:  # search for the start of the next record
                if l[0] in ">@":  # fasta/q header line
                    last = l[:-1]  # save this line
                    break
        if not last:
            break
        name, seqs, last = last[1:].partition(" ")[0], [], None
        for l in fp:  # read the sequence
            if l[0] in "@+>":
                last = l[:-1]
                break
            seqs.append(l[:-1])
        if not last or last[0] != "+":  # this is a fasta record
            yield name, "".join(seqs), None  # yield a fasta record
            if not last:
                break
        else:  # this is a fastq record
            seq, leng, seqs = "".join(seqs), 0, []
            for l in fp:  # read the quality
                seqs.append(l[:-1])
                leng += len(l) - 1
                if leng >= len(seq):  # have read enough quality
                    last = None
                    yield name, seq, "".join(seqs)
                    # yield a fastq record
                    break
            if last:  # reach EOF before reading enough quality
                yield name, seq, None  # yield a fasta record instead
                break


def sort_permissions(fl):
    # Need to ensure proper file permissions on output data
    # If users are running pipeline through Docker might otherwise require root access
    if oct(os.stat(fl).st_mode)[4:] != "666":
        os.chmod(str(fl), 0o666)


def read_index_single_file(inputargs):

    suffix = "." + inputargs["extension"]

    failed = open("Undetermined" + suffix, "w")

    outputreads = coll.Counter()
    outputreads["Undetermined"] = 0

    usedindexes = coll.defaultdict(
        list
    )  # This keeps a track of all files that have been generated to house demultiplexed reads

    XXdict = {}

    indexes = list(open(inputargs["indexlist"], "r"))

    for x in indexes:

        if x == "\n":
            print("Empty line detected in index file, presumed end of file.")
            break

        elements = x.strip("\n").split(",")
        sample = elements[0]

        open(sample + suffix, "w").close()

        compound_index = X1dict[elements[1]] + X2dict[elements[2]]
        XXdict[compound_index] = open(sample + suffix, "a")

        outputreads[sample] = 0
        usedindexes[sample] = compound_index

    return XXdict, outputreads, usedindexes, failed


def read_index_dual_file(inputargs):

    suffix = "." + inputargs["extension"]

    failed1 = open("Undetermined_R1" + suffix, "w")
    failed2 = open("Undetermined_R2" + suffix, "w")
    outputreads = coll.Counter()
    outputreads["Undetermined"] = 0

    usedindexes = coll.defaultdict(
        list
    )  # This keeps a track of all files that have been generated to house demultiplexed reads

    XXdict1 = {}

    for line in open(inputargs["indexlist"], "r"):

        if line == "\n":
            print("Empty line detected in index file, presumed end of file.")
            break

        elements = [y.strip() for y in line.split(",")]

        sample = elements[0]
        # note reverse complement of index one
        index1 = revcomp(elements[1])
        index2 = elements[2]

        # open(sample + "_R1" + suffix, "w").close()
        # open(sample + "_R2" + suffix, "w").close()
        compound_index = index2 + index1

        XXdict1[compound_index] = sample + "_R1" + suffix

        outputreads[sample] = 0
        usedindexes[sample] = compound_index

    return XXdict1, outputreads, usedindexes, failed1, failed2


###############################################
############# SEQUENCE PROCESSING #############
###############################################


def revcomp(x):
    return str(Seq(x).reverse_complement())


inputargs = vars(args())

if inputargs["outputall"] == False and not inputargs["indexlist"]:
    print(
        "No indexing file provided, and output all option not enabled; one (or both) is required."
    )
    sys.exit()

for f in [inputargs["read1"], inputargs["read2"], inputargs["index1"]]:
    if fastq_check(f) == False:
        print(
            "FASTQ sanity check failed reading",
            f,
            "- please ensure that this file is properly formatted and/or gzip compressed.",
        )
        sys.exit()

##########################################################
############ CREATE DICTIONARIES FOR INDEXES #############
##########################################################

# Version 4.0.1 (and above) introduces new SP2 indexes 27-102

# SP1 index = R1 (our own, RC1 proximal index)
X1dict = {
    "1": "ATCACG",
    "2": "CGATGT",
    "3": "TTAGGC",
    "4": "TGACCA",
    "5": "ACAGTG",
    "6": "GCCAAT",
    "7": "CAGATC",
    "8": "ACTTGA",
    "9": "GATCAG",
    "10": "TAGCTT",
    "11": "GGCTAC",
    "12": "CTTGTA",
    "13": "TAGACT",
}
# NB: One index removed due to similarity to others, but exists in earlier datasets: "14":"ACACGG"

# 'SP2' index = R2 (index read, comes first in rearranged sequence)
X2dict = {
    "1": "CGTGAT",
    "2": "ACATCG",
    "3": "GCCTAA",
    "4": "TGGTCA",
    "5": "CACTGT",
    "6": "ATTGGC",
    "7": "GATCTG",
    "8": "TCAAGT",
    "9": "CTGATC",
    "10": "AAGCTA",
    "11": "GTAGCC",
    "12": "TACAAG",
    "13": "TTGACT",
    "14": "GGAACT",
    "15": "CCTGGTAG",
    "16": "TAAGCATG",
    "17": "AGATGTGC",
    "18": "GTCGAGCA",
    "19": "GAATTGCT",
    "20": "AAGCAACT",
    "21": "CTAACTGG",
    "22": "AGGCTCAA",
    "23": "CAGTTGGT",
    "24": "TCTGGACC",
    "25": "TGTTATAC",
    "26": "TCAGCGAA",
    "27": "ACATAGCG",
    "28": "TGTGCTTA",
    "29": "GATGTTAC",
    "30": "GTCTTAGT",
    "31": "GAGTTACA",
    "32": "CCATTGTT",
    "33": "TGCGAAGG",
    "34": "CAACGGTC",
    "35": "CTTGCAGA",
    "36": "AGGATGTG",
    "37": "TAGATCCT",
    "38": "TAGATGAC",
    "39": "CTAGGTTC",
    "40": "GTGCGTAA",
    "41": "TCGCACCT",
    "42": "CGATCATG",
    "43": "GTTGCGGC",
    "44": "AGATATAA",
    "45": "CGCCACAG",
    "46": "AATGCGTT",
    "47": "GTCAAGTT",
    "48": "GGAAGGCG",
    "49": "TCCTGGTC",
    "50": "ACCAAGGA",
    "51": "AGTGTCTT",
    "52": "GATTACAG",
    "53": "ACTTCTTC",
    "54": "GTTCATTA",
    "55": "TTGCTGGA",
    "56": "CTGTGGAC",
    "57": "GACTATTG",
    "58": "CCTTACCT",
    "59": "GCTAAGTA",
    "60": "CTTCCTTC",
    "61": "TCGCTATG",
    "62": "CAGACAAT",
    "63": "GAGAGTTG",
    "64": "CCTAGAAT",
    "65": "CAGCAGCA",
    "66": "GGCTAGGC",
    "67": "GGCATAGG",
    "68": "GACGCTAT",
    "69": "ATCCGACA",
    "70": "TTACTGTC",
    "71": "TCGACGGC",
    "72": "CCTGGATA",
    "73": "AACATAAT",
    "74": "AATGTTGG",
    "75": "TGGATATC",
    "76": "TACTTGCA",
    "77": "AGAACATT",
    "78": "TACCGCTG",
    "79": "AGAGGAAT",
    "80": "ATCCGCAG",
    "81": "CATCAGAC",
    "82": "GGCAGATA",
    "83": "GATCGTGT",
    "84": "AGCTCTGG",
    "85": "GTTAGGTC",
    "86": "CAAGGCGA",
    "87": "ATGGTAGG",
    "88": "TCTAGCGA",
    "89": "ACATCCTT",
    "90": "CGAGTTAG",
    "91": "ATACCTGT",
    "92": "GACCGAGA",
    "93": "TCAACTGT",
    "94": "ACGCATAG",
    "95": "GGCTCCTG",
    "96": "TGCGACCT",
    "97": "CCTTGCTG",
    "98": "TTGATAAT",
    "99": "CTGATTAA",
    "100": "TGGTAACG",
    "101": "CTCTACTT",
    "102": "CTATTCAA",
}

##########################################################
########### GENERATE SAMPLE-NAMED OUTPUT FILES ###########
##########################################################

suffix = "." + inputargs["extension"]

# If given an indexlist, use that to generate named output files
if inputargs["indexlist"]:
    # if two index files submitted
    if inputargs["index2"]:
        XXdict1, outputreads, usedindexes, failed1, failed2 = (
            read_index_dual_file(inputargs)
        )
        sample_names = list(outputreads.keys())
        # print(sample_names)
        # exit()
    # if one index file sumbitted
    else:
        XXdict, outputreads, usedindexes, failed = read_index_single_file(
            inputargs
        )

###############################################################################################################
# If the outputall option is chosen, output all possible index combinations that exist in the data
# Note that if an indexlist is provided, those names are still used in the appropriate output files
# Also note that while all combinations are looked for, those which remain unused at the end will be deleted

if inputargs["outputall"] == True:

    # generate all possible index combinations, and then check if they have been generated yet (via an index file)
    # only make those that haven't
    allXcombs = [x + "-" + y for x in X1dict.keys() for y in X2dict.keys()]

    for x in allXcombs:
        compound_index = X1dict[x.split("-")[0]] + X2dict[x.split("-")[1]]

        if compound_index not in usedindexes.values():
            XXdict1[compound_index] = open("Indexes_" + x + suffix, "a")
            outputreads["Indexes_" + x] = 0
            usedindexes["Indexes_" + x] = compound_index
####################################################################################################################
if __name__ == "__main__":
    count = 0
    dmpd_count = 0  # number successfully demultiplexed
    fuzzy_count = 0  # number of sequences that were demultiplexed using non-exact index matches
    clash_count = 0  # number of fuzzy ID clashes

    fuzzies = []  # list to record IDs matched using fuzzy indexes

    print("Running Demultiplexor version", metadata.version("decombinator"))
    t0 = time.time()  # Begin timer

    ##########################################################
    ########### LOOP THROUGH ALL READ FILES IN SYNC ##########
    ######## PROCESS INTO CORRECT FORMAT & DEMULTIPLEX #######
    ##########################################################

    print("Reading input files...")

    # Open read files
    if inputargs["read1"].endswith(".gz"):
        fq1 = readfq(gzip.open(inputargs["read1"], "rt"))
    else:
        fq1 = readfq(open(inputargs["read1"]))

    if inputargs["index1"].endswith(".gz"):
        fq2 = readfq(gzip.open(inputargs["index1"], "rt"))
    else:
        fq2 = readfq(open(inputargs["index1"]))

    if inputargs["read2"].endswith(".gz"):
        fq3 = readfq(gzip.open(inputargs["read2"], "rt"))
    else:
        fq3 = readfq(open(inputargs["read2"]))

    if inputargs["index2"]:
        if inputargs["index2"].endswith(".gz"):
            fq4 = readfq(gzip.open(inputargs["index2"], "rt"))
        else:
            fq4 = readfq(open(inputargs["index2"]))

    print("Demultiplexing data...")

    if inputargs["index2"]:
        fqs = (fq1, fq2, fq3, fq4)
        zipfqs = zip(fq1, fq2, fq3, fq4)
    else:
        fqs = (fq1, fq2, fq3)
        zipfqs = zip(fq1, fq2, fq3)

    #  for record1, record2, record3 in zip(fq1, fq2, fq3):
    for records in zipfqs:

        if inputargs["index2"]:
            record1, record2, record3, record4 = records
        else:
            record1, record2, record3 = records

        # Readfq function will return each read from each file as a 3 part tuple
        # ('ID', 'SEQUENCE', 'QUALITY')
        count += 1

        #   if count % 100000 == 0 and inputargs['dontcount'] == False:
        if count % 1000 == 0 and inputargs["dontcount"] == False:
            print("\t read", count)

            # os.unlink(f + "_R1"+ suffix)
        ####################################################################################
        #      exit()

        ### NB For non-standard Illumina encoded fastqs, might need to change which fields are carried into fq_* vars

        fq_id = record1[0]

        # N relates to barcode random nucleotides, X denotes index bases

        ### FORMATTING OUTPUT READ ###

        # Assume second index embedded within record1
        if len(records) == 3:

            Nseq = record3[1][0:45]
            Nqual = record3[2][0:45]

            X1seq = record1[1][6:12]
            X1qual = record1[2][6:12]

            X2seq = record2[1]
            X2qual = record2[2]

            readseq = record1[1][12:]
            readqual = record1[2][12:]

            fq_seq = Nseq + X1seq + X2seq + readseq
            fq_qual = Nqual + X1qual + X2qual + readqual

            new_record = str(
                "@" + fq_id + "\n" + fq_seq + "\n+\n" + fq_qual + "\n"
            )

            seqX = X1seq + X2seq

        # for double index just save R1 and R2 separately
        if len(records) == 4:

            # Nseq = record3[1][0:45]
            # Nqual = record3[2][0:45]

            X1seq = record4[1]
            X1qual = record4[2]

            X2seq = record2[1]
            X2qual = record2[2]

            readseq = record1[1]
            readqual = record1[2]

            # fq_seq = Nseq + X1seq + X2seq + readseq
            # fq_qual = Nqual + X1qual + X2qual + readqual

            new_record1 = str(
                "@" + fq_id + "\n" + record1[1] + "\n+\n" + record1[2] + "\n"
            )
            new_record2 = str(
                "@" + fq_id + "\n" + record3[1] + "\n+\n" + record3[2] + "\n"
            )
            seqX = X1seq + X2seq

        ### DEMULTIPLEXING ###
        # print(outputreads.keys())

        if seqX in XXdict1:
            # Exact index matches
            filename_1 = open(XXdict1[seqX], "a")
            filename_1.write(new_record1)
            filename_1.close()
            filename_2 = open(XXdict1[seqX].replace("R1.f", "R2.f"), "a")
            filename_2.write(new_record2)
            filename_2.close()
            dmpd_count += 1
            outputreads[XXdict1[seqX]] += 1
            # Sprint(sample_names)
        else:
            # Otherwise allow fuzzy matching

            matches = []

            for ndx in XXdict1.keys():

                if lev.distance(ndx, seqX) <= inputargs["threshold"]:
                    matches.append(ndx)

            if len(matches) == 1:
                # Only allow fuzzy match if there is one candidate match within threshold
                # print("fuzzy")
                filename_1 = open(XXdict1[matches[0]], "a")
                filename_2 = open(
                    XXdict1[matches[0]].replace("R1.f", "R2.f"), "a"
                )

                # print(filename_1)
                filename_1.write(new_record1)
                filename_1.close()
                filename_2.write(new_record2)
                filename_2.close()
                dmpd_count += 1
                fuzzy_count += 1
                fuzzies.append(fq_id)
                # print(XXdict1[matches[0]])
                # exit()
                outputreads[XXdict1[matches[0]]] += 1

            else:

                if len(matches) > 1:
                    clash_count += 1

                failed1.write(new_record1)
                failed2.write(new_record2)
                outputreads["Undetermined"] += 1

    for x in XXdict1.values():
        open(x).close
        sort_permissions(open(x).name)

    failed1.close()
    failed2.close()
    sort_permissions(failed1.name)
    sort_permissions(failed2.name)
    for f in fqs:
        f.close()

    # If output all is allowed, delete all unused index combinations
    if inputargs["outputall"] == True:
        for f in outputreads.keys():
            if outputreads[f] == 0:
                os.remove(f + suffix)
                del outputreads[f]
                del usedindexes[f]

    # Gzip compress output

    ##########################################################################################################################

    if inputargs["dontgzip"] == False:
        print("Compressing demultiplexed files...")
        for f in sample_names:
            # print(f)
            with (
                open(f + "_R1" + suffix) as infile,
                gzip.open(
                    f + "_R1" + suffix + ".gz",
                    "wt",
                    compresslevel=inputargs["compresslevel"],
                ) as outfile,
            ):
                outfile.writelines(infile)
                sort_permissions(outfile.name)
                print(
                    f + "_R1" + suffix,
                    "compressed to",
                    f + "_R1" + suffix + ".gz",
                )
            try:
                os.remove(f + "_R1" + suffix)
                # print("works")
            except:
                continue
            with (
                open(f + "_R2" + suffix) as infile,
                gzip.open(
                    f + "_R2" + suffix + ".gz",
                    "wt",
                    compresslevel=inputargs["compresslevel"],
                ) as outfile,
            ):
                outfile.writelines(infile)
                sort_permissions(outfile.name)
                print(
                    f + "_R2" + suffix,
                    "compressed to",
                    f + "_R2" + suffix + ".gz",
                )
            try:
                os.remove(f + "_R2" + suffix)
                # print("works")
            except:
                continue

    #################################################
    ################## STATISTICS ###################
    #################################################

    timed = time.time() - t0
    took = round(timed, 2)
    # print(count, 'reads processed from', rd1file, 'and', fq2file, 'and output into', outfq #FIX)
    if took < 60:
        print("\t\t\t\t\t\t\tTook", took, "seconds to demultiplex samples")
    else:
        print(
            "\t\t\t\t\t\t\tTook",
            round((timed / 60), 2),
            "minutes to jimmy indexes and hexamers around",
        )

    print(count, "reads processed")
    print(dmpd_count, "reads demultiplexed")
    print(fuzzy_count, "reads demultiplexed using fuzzy index matching")

    if clash_count > 0:
        print(
            clash_count,
            "reads had fuzzy index clashes (i.e. could have assigned to >1 index) and were discarded",
        )

    # Write data to summary file
    if inputargs["suppresssummary"] == False:

        # Check for directory and make summary file
        if not os.path.exists("Logs"):
            os.makedirs("Logs")
        date = time.strftime("%Y_%m_%d")

        # Check for existing date-stamped file
        summaryname = "Logs/" + date + "_Demultiplexing_Summary.csv"
        if not os.path.exists(summaryname):
            summaryfile = open(summaryname, "w")
        else:
            # If one exists, start an incremental day stamp
            for i in range(2, 10000):
                summaryname = (
                    "Logs/"
                    + date
                    + "_Demultiplexing_Summary_"
                    + str(i)
                    + ".csv"
                )
                if not os.path.exists(summaryname):
                    summaryfile = open(summaryname, "w")
                    break

        # Generate string to write to summary file

        summstr = (
            "Property,Value\nDirectory,"
            + os.getcwd()
            + "\nDateFinished,"
            + date
            + "\nTimeFinished,"
            + time.strftime("%H:%M:%S")
            + "\nTimeTaken(Seconds),"
            + str(round(timed, 2))
            + "\n"
        )

        for s in [
            "read1",
            "read2",
            "index1",
            "indexlist",
            "extension",
            "threshold",
            "outputall",
            "dontgzip",
            "fuzzylist",
        ]:
            summstr = summstr + s + "," + str(inputargs[s]) + "\n"

        summstr = (
            summstr
            + "NumberReadsInput,"
            + str(count)
            + "\nNumberReadsDemultiplexed,"
            + str(dmpd_count)
            + "\nNumberFuzzyDemultiplexed,"
            + str(fuzzy_count)
            + "\nNumberIndexClash,"
            + str(clash_count)
            + "\n\nOutputFile,IndexUsed\n"
        )

        # Write out number of reads in and details of each individual output file
        for x in sorted(usedindexes.keys()):
            summstr = summstr + x + "," + usedindexes[x] + "\n"

        if inputargs["indexlist"]:
            summstr = summstr + "\nOutputFile,IndexNumbersUsed(SP1&SP2)\n"
            indexes = list(open(inputargs["indexlist"], "r"))
            for x in indexes:
                splt = x.rstrip().split(",")
                summstr = (
                    summstr + splt[0] + "," + splt[1] + " & " + splt[2] + "\n"
                )

        summstr = summstr + "\nOutputFile,NumberReads\n"

        for x in sorted(outputreads.keys()):
            summstr = summstr + x + "," + str(outputreads[x]) + "\n"

        print(summstr, file=summaryfile)

        summaryfile.close()
        sort_permissions(summaryname)

    # Write out list of fuzzy matched sequences, so can fish out later if needed
    if inputargs["threshold"] > 0 and inputargs["fuzzylist"] == True:

        print(
            "\nOutputting list of reads demultiplexed using fuzzy index matching"
        )

        # Check for directory and make summary file
        if not os.path.exists("Logs"):
            os.makedirs("Logs")
        date = time.strftime("%Y_%m_%d")

        fuzzname = "Logs/" + date + "_FuzzyMatchedIDs.txt"
        fuzzout = open(fuzzname, "w")
        for f in fuzzies:
            print(f, file=fuzzout)

        fuzzout.close()
        sort_permissions(fuzzname)
