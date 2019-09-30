# Decombinator 
# James M. Heather, August 2016, UCL
# https://innate2adaptive.github.io/Decombinator/

##################
### BACKGROUND ###
##################

# Searches FASTQ reads (produced through Demultiplexor.py) for rearranged TCR chains
# Can currently analyse human and mouse TCRs, both alpha/beta and gamma/delta chains
  # NB: Human alpha/beta TCRs are the most thoroughly tested, due to the nature of the data we generated. YMMV.

# Current version (v3) is optimised for interpretation of data generated using our wet lab protocol, but could be modified to work on any data.

# Script represents improvements upon a combination of the two previously in use Decombinator versions
  # i.e. Decombinator V2.2 (written primarily by Nic Thomas, see Thomas et al, Bioinformatics 2013, DOI: 10.1093/bioinformatics/btt004)
  # and vDCR (which was v1.4 modified by James Heather, see Heather et al, Frontiers in Immunology 2016, DOI: 10.3389/fimmu.2015.00644)
  # Now faster, more accurate and easier to use than either of the previous versions.
  
##################
###### INPUT #####
##################

# As with entire pipeline, Decombintator is run using command line arguments to provide user parameters
  # All arguments can be read by viewing the help data, by running python Decombintator.py -h

# Takes FASTQ reads produced by Demultiplexor.py (unzipped or gzipped), which is the minimum required command line input, using the -fq flag
  # NB: Data must have been generated using the appropriate 5'RACE ligation protocol, using the correct SP2-I8-6N-I8-6N oligonucleotide

# The TCR chain locus to look for can be explicitly specified using the -c flag 
  # Users can use their choice of chain identifiers from this list (case insensitive): a/b/g/d/alpha/beta/gamma/delta/TRA/TRB/TRG/TRD/TCRA/TCRB/TCRG/TCRD
  # If no chain is provided (or if users which to minimise input arguments), script can infer chain from the FASTQ filename
    # I.e. "alpha_sample.fq" would be searched for alpha chain recombinations
    # NB: This autodetection only works if there is only ONE TCR locus present in name (which must be spelt out in full)

# Other optional flags:
  
  # -s/--supresssummary: Supress the production of a summary file containing details of the run into a 'Logs' directory. 
      
  # -dz/--dontgzip: Suppress the automatic compression of output demultiplexed FASTQ files with gzip. 
    # Using this flag makes the script execute faster, but data will require more storage space. 
    
  # -dc/--dontcount: Suppress the whether or not to show the running line count, every 100,000 reads. 
    # Helps in monitoring progress of large batches.
  
  # -dk/--dontcheck: Suppress the FASTQ sanity check. 
    # Strongly recommended to leave alone: sanity check inspects first FASTQ read for basic FASTQ parameters.
  
  # -pf/--prefix: Allows users to specify the prefix of the Decombinator TCR index files produced. Default = 'dcr_'
  
  # -ex/--extension: Allows users to specify the file extension of the Decombinator TCR index files produced. Default = '.n12'

  # -or/--orientation: Allows users to specify which DNA orientations to check for TCR reads. Default = reverse only, as that's what the protocol produces.
    # This will likely need to be changed for analysing data produced by protocols other than our own.

  # -tg/--tags: Allows users to specify which tag set they wish to use. For human alpha/beta TCRs, a new 'extended' tag set is recommended, as it covers more genes.
    # Unfortunately an extended tag set is only currently available for human a/b genes.

  # -sp/--species: Current options are only human or mouse. Help could potentially be provided for generation of tags for different species upon request.
  
  # -N/--allowNs: Provides users the option to allow 'N's (ambiguous base calls), overriding the filter that typically removes rearrangements that contain them.
    # Users are recommended to not allow Ns, as such bases are both themselves low quality data and predict reads that are generally less trustworthy.
    
  # -ln/--lenthreshold: The length threshold which (the inter-tag region of) successful rearrangements must be under to be accepted. Default = 130.
  
  # -tfdir/--tagfastadir: The path to a local copy of a folder containing the FASTA and Decombinator tag files required for offline analysis.
    # Ordinarily such files can be downloaded on the fly, reducing local clutter.
    # By default the script looks for the required files in the present working directory, then in a subdirectory called "Decombinator-Tags-FASTAs", then online.
    # Files are hosted on GitHub, here: https://github.com/innate2adaptive/Decombinator-Tags-FASTAs

  # -nbc/--nobarcoding: Run Decombinator without any barcoding, i.e. use the whole read. 
    # Recommended when running on data not produced using the Innate2Adaptive lab's ligation-mediated amplification protocol

##################
##### OUTPUT #####  
##################

# Produces a '.n12' file by default, which is a standard comma-delimited Decombinator output file with several additional fields:
  # V index, J index, # V deletions, # J deletions, insert, ID, TCR sequence, TCR quality, barcode sequence, barcode quality
  # NB The TCR sequence given here is the 'inter-tag' region, i.e. the sequence between the start of the found V tag the end of the found J tag 

##################
#### PACKAGES ####  
##################
print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
print ""
print "The code here has been deleted and no longer exists in this branch!"
print ""
print "This was a quick example to show that we can have different functionality in different"
print "branches, while always working from the same directory. The code is deleted in this"
print "branch, but still exists in the main branch."
print ""
print "In reality, this script would still contain the Decombinator code but likely with new"
print "upgraded functionality. Switching to this branch provides an easy means for multiple"
print "people to test or change the software during development. Once the changes are ready to"
print "roll out, the development branch will be merged into the master branch. The master"
print "branch would then be complete with the latest changes, ready for anyone to use as the"
print "most 'up-to-date' version of Decombinator!"
print ""
print "This is part of the Decombinator tutorial 07/10/2019"
print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
