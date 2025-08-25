import os
from typing import Dict, Any
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

class BlastDB(str, Enum):
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
        Given the source_str and fragment_bool, return the correct Enum _value_.
        """
        enum_str = source_str.upper()
        if fragment_bool:
            enum_str += "_NF"
        return cls[enum_str].value

# remove dict keys whose values are None; this happens when a parameter group
# is left un-enabled but is required?
def clean_dict(parameter_dict: Dict[str,Any]) -> Dict[str,Any]:
    """ Helper to remove parameter keys that are left blank in the KBase UI """
    try:
        for key, value in parameter_dict.items():
            if value == None:
                parameter_dict.pop(key)
    except AttributeError:
        pass
    return parameter_dict

# create a namedtuple object that will contain key-subkey pairs needed to
# cleanly access parameters stashed in KBase's "parameter-groups" subdicts.
# Third argument is the nextflow parameter name that the UI parameter should
# map to; if left as an empty string, no mapping to a params.json file is used.
KBaseMapping = namedtuple(
    "Mapping",  # the object name used in __str__ and __repr__
    ["dict_key", "subdict_key", "nf_parameter_name"] # list are accepted args
)

# create a general purpose function to get the value from a nested
# parameter_dict object based on the input KBaseMapping object.
def get_param_value(parameter_dict: Dict[str,Any], mapping: KBaseMapping):
    """
    Helper to safely get a value from the twice-nested KBase parameter_dict
    where the outer dict contains parameter_groups and inner subdicts contain
    the parameters defined within each group.
    """
    try:
        return parameter_dict.get(mapping.dict_key,{}).get(mapping.subdict_key)
    except AttributeError:
        raise AttributeError(f"parameter_dict['{mapping_dict_key}'] value is not a dict.")

def apply_mapping(parameter_dict: Dict[str, Any], mapping: KBaseMapping):
    """
    Helper to safely apply the mapping of KBase parameter dict/subdict pairs to
    the nextflow pipeline parameter name.
    """
    val = get_param_value(parameter_dict, mapping)
    if val and mapping.nf_parameter_name:
        return {mapping.nf_parameter_name: val}
    
    return {}

