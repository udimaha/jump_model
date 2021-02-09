# 'Jump Model' Swiss Knife
## Utilities for simulating and matching data against the evolutionary "Jump Model" [CITATION MISSING]

* [Acknowledgement](#acknowledgement)
* [Getting started](#getting-started)
* [Utilities](#utilities)
   * [Simulate](#simulate)
      * [Usage:](#usage)
      * [Output:](#output)
      * [Example:](#example)
   * [Tabulate](#tabulate)
      * [Usage](#usage-1)
      * [Example:](#example-1)
   * [RealData](#realdata)
      * [Parsing eggNOG CSVs into a single JSON file](#parsing-eggnog-csvs-into-a-single-json-file)
         * [Example:](#example-2)
      * [Creating occurrences CSV's from the parsed JSON file:](#creating-occurrences-csvs-from-the-parsed-json-file)
      * [Draw images based on the distribution of occurrences from the parsed JSON file:](#draw-images-based-on-the-distribution-of-occurrences-from-the-parsed-json-file)
   * [Likelihood](#likelihood)
      * [Usage:](#usage-2)
   * [Averages](#averages)
      * [Usage](#usage-3)
   * [MakePlots](#makeplots)
      * [Usage](#usage-4)
   * [MergePlots](#mergeplots)
      * [Usage](#usage-5)
* [Developing](#developing)
   * [Adding a new python package](#adding-a-new-python-package)
   * [Testing](#testing)

This repository contains several utilities which simulate an evolutionary process and matches 
it against real biological data.

## Acknowledgement
Suffix tree implementation was adapted from Peter Us' code: 
https://github.com/ptrus/suffix-trees

## Getting started
Clone the repository:
> git clone https://github.com/tomfeigin/jump_model.git

Step into the cloned repository
> cd jump_model

Create a Python3 virtual environment:<br>
_Further reading here: https://docs.python.org/3/tutorial/venv.html_
> python3 -m venv venv

Activate the virtual environment:
> source venv/bin/activate

Use pip to install the Python requirements:
> pip install -r requirements.txt

Now you can start developing!

## Utilities

### Simulate
This utility runs a simulation of the jump model producing a zipped JSON file as the result.
The simulation constructs a YuleTree model where the edge lengths of the tree are taken from an exponential 
distribution according to an input `scale` parameter. <br>
After constructing the tree, a "genome" is propagated from the 
root to the leaves while optionally mutating it at each inheritance step.<br>
The longer an edge length, the more probable that a gene will "jump" during the inheritance of the genome to that node<br>
When a "jump" occurs the size of the jumping group is determined according to a
geometric distribution generated according to the `alpha` parameter.<br>
The leaves of the tree are taken as genomes of a simulated population, the genomes are used as sequences of 
integers (representing genes) to construct a general suffix tree. <br>
The suffix tree is used to count the number of occurrences of each shared subsequence for each subsequence length. <br>
#### Usage:
> python Simulate.py CONFIG_FILE

#### Output:
The resulting file has the following structure:
```json
{
    "model": {
      "newick": "(A:0.1,B:0.2,(C:0.3,D:0.4):0.5);",
      "edge_count": 0,
      "median_edge_len": 0.0,
      "average_edge_len": 0.0
    },
    "genome_size": 4096,
    "total_jumps": 17,
    "avg_jumps": 10.0,
    "expected_edge_len": 0.5,
    "leaves_count": 256,
    "seed": 1234,
    "occurrences": {
      "2": [2,2,2,3],
      "10": [3,4,4]
    },
    "alpha": 0.5
}
```
- `model` - Holds data related to the construction of the tree:
    - `newick` - The resulting tree represented in Newick format
    - `edge_count` - The number of edges in the tree.
    - `median_edge_len` - The median edge length.
    - `average_edge_len` - The average edge length.
- `genome_size` - The number of genes in each genome.
- `total_jumps` - The total number of jump events which occurred during the simulation.
- `avg_jumps` - The average number of jump events in a single inheritance step.
- `expected_edge_len` - The expected edge length for the constructed tree (the scale parameter of the exponential distribution).
- `leaves_count` - Number of leaves in the generated tree.
- `seed` - Value used to seed the random number generator.
- `occurrences` - A dictionary containing the list of common occurrences for each word size.
- `alpha` - The alpha argument used to determine the size of the "jumping" group.


The simulation reads parameters from a configuration file, an example file can be found in: [Code Directory](configurations/sample_simulate.json).
#### Example:
```json
{
  "data_path": "~/jump_model/data/genes/",
  "tree_count": 70,
  "alpha": 1,
  "genome_size": 4096,
  "leaf_count": 256,
  "processes": 20,
  "scale": [0.1, 0.6, 0.1],
  "ultrametric": true
}
```
- `data_path` - Output directory
- `tree_count` - Generates a JSON file for each tree
- `alpha` - The alpha parameter (0 < alpha <= 1.0)
- `genome_size` - Number of genes in each genome
- `leaf_count` - The number of leaves in the tree (each leaf represents a genome).
- `processes` - Number of processes to use for concurrency.
- `scale` - The scale used to determining the exponential distribution of the edge lengths. Starting from 0.1 up to (and including 0.6), advancing by 0.1 each step.
- `ultrametric` - If `false`, the tree is constructed by adding two child nodes for a randomly selected leaf until the number of leaves in the tree equals `leaf_count`. 
  If set to `true`, the tree is constructed by "hanging" a new father for a randomly selected leaf and creating a new siebling for it, thus keeping the edge lengths more evenly distributed. 

### Tabulate
This utility is used to convert the JSON file produced by the `Simulate` utility into CSV files

#### Usage
> python Tabulate.py CONFIG_FILE

The utility reads parameters from a configuration file, an example file can be found in: [Code Directory](configurations/sample_tabulate.json).
#### Example:
```json
{
  "data": "~/jump_model/data/genes",
  "output": "~/jump_model/data/distributions",
  "file_pattern": "*.gz",
  "processes": 20
}
```
- `data` - The path to the directory containing the JSON files produced by the `Simulate` utility.
- `output` - The directory to put the produced CSVs
- `file_pattern` - The pattern to match the JSON files to be parsed.
- `processes` - Number of processes to use for concurrency.

### RealData
This utility contains several subcommands used to parse real biological data into structures relevant for the Jump Model simulation <br>

#### Parsing eggNOG CSVs into a single JSON file
This subcommand reads parameters from a configuration file, an example file can be found in: [Code Directory](configurations/sample_realdata.json).<br>
The input CSVs are assumed to have the following fields: "Taxid", "Gene name", "Contig", "Srnd", "Start", "Stop", "Length", "Cog"  
> python RealData.py parse CONFIG_FILE
##### Example:
```json
{
  "real_data": "/tmp",
  "output": "/tmp"
}
```
- `real_data` - The path to the directory containing the "real data" files
- `output` - The path to create the resulting JSON file in.

#### Creating occurrences CSV's from the parsed JSON file:
> python RealData.py make_csvs DATA_FILE OUT_DIR MIN_OCCURRENCES MIN_DENSITY
- `DATA_FILE` - The resulting JSON file from the `parse` subcommand.
- `OUT_DIR` - The directory to put the resulting CSVs
- `MIN_OCCURRENCES` - The minimum number of occurrences to consider (set to 0 to consider all).
- `MIN_DENSITY` - The minimum density per occurrences to consider (set to 0 to consider all).

#### Draw images based on the distribution of occurrences from the parsed JSON file:
> python RealData.py draw DATA_FILE OUT_DIR
- `DATA_FILE` - The resulting JSON file from the `parse` subcommand.
- `OUT_DIR` - The directory to put the resulting PNGs

### Likelihood
This utility is used to calculate a probability "score" by comparing real biological data produced by the `RealData` utility to data produced by the `Tabulate` utility.<br>

#### Usage:
> python Likelihood.py SIMULATED_DIR SIMULATED_GLOB REALDATA_DIR REALDATA_GLOB [SIMULATED_REGEX = \d+] [REALDATA_REGEX = \d+]
- `SIMULATED_DIR` - Directory containing CSVs produced by the `Tabulate` utility.
- `SIMULATED_GLOB` - Glob pattern to match CSV files in the simulated directory.
- `REALDATA_DIR` - Directory containing CSVs produced by the `RealData` utility.
- `REALDATA_GLOB` - Glob pattern to match CSV files in the realdata directory.
- `SIMULATED_REGEX` - Optional. The regex used to extract the word size from a CSV file name. Default = "\d+"
- `REALDATA_REGEX` - Optional. The regex used to extract the word size from a CSV file name. Default = "\d+"

### Averages
This utility calculates the average distribution of word occurrences from multiple JSON files produced by the `Simulate` subcommand.

#### Usage
> python Averages.py CONFIG_FILE

Sample configuration file can be found here: [Code Directory](configurations/sample_averages.json)

```json
{
  "data": "~/jump_model/data/genes",
  "output": "~/jump_model/data/distributions",
  "file_pattern": "*.gz",
  "processes": 20
}
```
- `data` - The path to the directory containing the JSON files produced by the `Simulate` utility.
- `output` - The directory to put the resulting averaged distributions at.
- `file_pattern` - The file pattern to match when looking for the JSON files to parse.
- `processes` - Number of processes to use for concurrency.

### MakePlots
This utility is used to create PNGs of distribution plots produced from the JSON files created by the `Averages` utility.<br>
The distribution plots will plot the data for the different expected edge lengths in the same image.

#### Usage
> python MakePlots.py DATA_PATH OUTPUT_PATH EDGE_LENGTHS
- `DATA_PATH` - The path to the directory containing the JSON files produced by the `Averages` utility.
- `OUTPUT_PATH` - The path to the directory to contain the produced images
- `EDGE_LENGTH` - The number of different expected edge lengths which the input JSON files include

### MergePlots
This utility is used to combine PNGs produced by the `MakePlots` utility into a single GIF file.

#### Usage
> python MergePlots.py OUTPUT_DIR OUTPUT_NAME VISUALIZED_PATH
- `OUTPUT_DIR` - The directory to contain the produced GIFs
- `OUTPUT_NAME` - The name to save the resulting GIF file in.
- `VISUALIZED_PATH` - The directory containing the PNG files produced by the `MakePlots` utility

## Developing
### Adding a new python package
To add a new python package add it the requirements.txt file

### Testing
Testing is done using pytest: https://docs.pytest.org
