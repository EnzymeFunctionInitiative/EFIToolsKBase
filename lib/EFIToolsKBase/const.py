import os
from enum import Enum
from collections import namedtuple

MODULE_DIR = "/kb/module"
TEMPLATES_DIR = os.path.join(MODULE_DIR, "lib/templates")

EFI_CONFIG_PATH = "/EST/efi.config"
EFI_DB_PATH = "/data/efi_db.sqlite"
EFI_DB_VERSION = 104

DEFAULT_NF_PARAMETERS = {
    "efi_config": EFI_CONFIG_PATH,
    "efi_db": EFI_DB_PATH,
    "duckdb_memory_limit": "8GB",
    "duckdb_threads": 1,
    "num_fasta_shards": 8,
    "num_accession_shards": 16,
    "multiplex": False,
}

class BlastDB(Enum):
    """
    Enum to enable clean handling of file paths for the Blast DB files. 
    """
    COMBINED = "/data/blastdb/combined.fasta"
    COMBINED_NF = "/data/blastdb/combined_nf.fasta"
    UNIREF90 = "/data/blastdb/uniref90.fasta"
    UNIREF90_NF = "/data/blastdb/uniref90_nf.fasta"
    UNIREF50 = "/data/blastdb/uniref50.fasta"
    UNIREF50_NF = "/data/blastdb/uniref50_nf.fasta"
    
    def __str__(self):
        """ Change the str representation to be the lowercased self.name """
        return self.name.lower()

    @classmethod
    def get_path(cls, source_str: str, fragment_bool: bool) -> Enum:
        """
        Given the source_str and fragment_bool, return the correct Enum value.
        """
        enum_str = source_str.upper()
        if fragment_bool:
            enum_str += "_NF"
        return cls[enum_str].value

# create a namedtuple object that will contain key, subkey pairs needed to 
# cleanly access the parameters associated with filters to be applied
_filter_keys = namedtuple(
    "filter", 
    ["dict_key", "subdict_key", "nf_filter_name"]
)

# make the specific filter_keys objects, one for each filter
fragment_filter = _filter_keys(
    "fragment_option", 
    "exclude_fragments", 
    "exclude_fragments"
)
family_filter = _filter_keys("filter_by_family","family_filter","family_filter")
fraction_filter = _filter_keys(
    "protein_family_addition_options",
    "fraction",
    "fraction"
)
# NOTE: make the equivalent for taxonomy filtering

# create an iterable for all filters
ALL_FILTERS = (fragment_filter, family_filter, fraction_filter)

# filter param subdict keys:
#   ["fragment_option"]["exclude_fragments"]
#   ["filter_by_family"]["family_filter"]
#   ["protein_family_addition_options"]["fraction"]
#   [""][""]
#   [""][""]

