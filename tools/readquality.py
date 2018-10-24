#!/usr/bin/env python3

import os
import sys
import argparse
import subprocess
import csv
from staphB_ToolKit.core import fileparser
from staphB_ToolKit.tools import taxon

class ReadQuality:
    #class object to contain fastq file information
    runfiles = None
    #path to fastq files
    path = None
    #output directory
    output_dir = None

    def __init__(self,runfiles=None, path, output_dir = ""):
        if runfiles:
            self.runfiles = runfiles
        else:
            self.path = path
            self.runfiles = fileparser.RunFiles(self.path)

        if output_dir:
            self.output_dir = output_dir
        else:
            self.output_dir = os.getcwd()

    def cg_pipeline(self, mash=True):
        cgp_output_dir = os.path.join(self.output_dir,"cg_pipeline_output")

        if not os.path.isdir(cgp_output_dir):
            os.makedirs(cgp_output_dir)
            print("Directory for cg_pipeline output made: ", cgp_output_dir)


        taxon = taxon.Taxon(self.name, self.output_dir)
        mash_species = taxon.mash()

        #data dictrionary containing quality metrics for each isolate
        #formatted id: {r1_q: X, r2_q: X, est_cvg: X}
        isolate_qual = {}

        for id in self.runfiles.ids:
            isolate_qual[id] = {"r1_q": None, "r2_q": None, "est_cvg": None}

            if 'Salmonella' in mash_species[id] or 'Escherichia' in mash_species[id]:
                genome_length = 5000000
            elif 'Campylobacter' in mash_species[id]:
                genome_length = 1600000
            elif 'Listeria' in mash_species[id]:
                genome_length = 3000000
            elif 'Vibrio' in mash_species[id]:
                genome_length = 4000000
            else:
                genome_length = input("What is the expected genome size of " + id + "?")
                try:
                    float(genome_length)
                except ValueError:
                   print("A number was not entered")

            cgp_out = cgp_output_dir + id + "_readMetrics.tsv"

            fwd = self.runfile.reads[id].fwd
            rev = self.runfile.reads[id].rev
            if "R1" in fwd:
                reads = fwd.replace("R1", "*")
            else:
                reads = fwd.replace("_1", "*")

            if not os.path.isfile(cgp_out):
                subprocess.call("run_assembly_readMetrics.pl --fast" + " " + reads + " " + "-e" + " "
                                + str(genome_length) + " > " + cgp_out + " ", shell=True)


            with open(cgp_out, "r") as tsv_file:
                tsv_reader = list(csv.DictReader(tsv_file, delimiter='\t'))

                for line in tsv_reader:
                    if fwd in line["File"]:
                        isolate_qual[id]["r1_q"] = line["avgQuality"]
                        isolate_qual[id]["est_cvg"] = float(line["coverage"])
                    if rev in line["File"]:
                        isolate_qual[id]["r2_q"] = line["avgQuality"]
                        isolate_qual[id]["est_cvg"] += float(line["coverage"])

        print(isolate_qual)
        return(isolate_qual)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(usage="readquality.py <input> [options]")
    parser.add_argument("input", type=str, help="path to dir containing read files")
    parser.add_argument("-o", default="", type=str, help="Name of output_dir")
    parser.add_argument("-cg_pipeline", action='store_true', help="Perform quality assessment using CG_Pipeline")


    if len(sys.argv[1:]) == 0:
        parser.print_help()
        parser.exit()
    args = parser.parse_args()

    path = args.input
    cg_pipeline = args.cg_pipeline
    output_dir = args.o

    if not output_dir:
        output_dir = path

    quality = ReadQuality(path, output_dir)
    print("Project selected: " + quality.path)

    if cg_pipeline:
        print(quality.cg_pipeline())