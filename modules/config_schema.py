from pathlib import Path
from schema import Schema, And, Or, Use, Optional, SchemaError

from modules.structs import DocumentSWType, DatabaseType
from modules.structs import Source

schema_wire = Schema({
    "name": str,
    "from": str,
    "to": str,
})

schema_source = {
    "name": str,
}

schema_source_plc = Schema({
    **schema_source,
    "plc": str, 
})

schema_source_library = Schema({
    **schema_source,
    "library": str, 
})


schema_sections_members_attributelist = Schema({
    "BooleanAttribute": list[dict],
})

schema_sections_members = Schema({
    "Name": str,
    "Datatype": str,
    Optional("attributes", default={}): dict, # rename back to "AttributeList" if something crashes in xml_builder.py lol
})

schema_sections = Schema({
    "name": str,
    "members": [schema_sections_members],
})

schema_multi_instance_db = Schema({
    "type": And(str, Use(DatabaseType)),
    "component_name": str,
    Optional("sections", default=[]): And(list, [schema_sections]),
    Optional("wires", default={}): And(list, list[schema_wire]),
})





###


schema_plcblock = {
    "type": And(str, Use(DocumentSWType)),
    "name": str,
    Optional("folder", default=[]): And(list, [str]),
    Optional("number", default=1): int,
}

schema_db = Schema({
    "type": And(str, Use(DatabaseType)),
    "name": str,
})

schema_instancedb = Schema({
    **schema_db.schema,
    Optional("folder", default=[]): And(list, [str]),
    Optional("number", default=1): int,
})

schema_db_data = Schema({
    "name": str,
    "datatype": str,
    Optional("retain", default=True): bool,
    Optional("attributes", default={}): dict
})

schema_globaldb = Schema({
    **schema_instancedb.schema,
    Optional("data", default={}): list,
    Optional("attributes", default={}): dict,
})

schema_multi_instance_db = Schema({
    "type": And(str, Use(DatabaseType)),
    "data": dict
})

schema_instance_source = Schema({
    "source": Use(Source),
    "type": And(str, Use(DocumentSWType)),
    "name": str,
    Optional("from_folder", default=[]): And(list, [str]),
    Optional("to_folder", default=[]): And(list, [str]),
    Optional("db"): schema_instancedb,

})

schema_instance_library = Schema({
    **schema_instance_source.schema,
    "library": str,
})

schema_ob_fb_fc = {
    **schema_plcblock,
    "programming_language": str,
    Optional("db"): schema_instancedb,
}

schema_network_source = {
    Optional("instances", default=[]): [Or(Schema(schema_instance_source), schema_instance_library, Schema(schema_ob_fb_fc))],
    Optional("title", default=""): str,
    Optional("comment", default=""): str,
}

schema_network_source.update({
    Optional("instances", default=[]): [Or(Schema(schema_instance_source), schema_instance_library, Schema(schema_ob_fb_fc))],
})

schema_ob_fb_fc.update({
    Optional("network_sources", default=[]): [Schema(schema_network_source)],
})

schema_network_source.update({
    Optional("instances", default=[]): [Or(Schema(schema_instance_source), schema_instance_library, Schema(schema_ob_fb_fc))],
})









schema_plc_tag = Schema({
        "Name": str,
        "DataTypeName": str,
        "LogicalAddress": str,
    })

schema_plc_tag_table = Schema({
        "Name": str,
        Optional("Tags", default=[]): [schema_plc_tag],
    })

schema_plc_data_types = Schema({
    "Name": str,
    Optional("types", default=[]): [schema_sections_members],
})

schema_module = Schema({
        "TypeIdentifier": str,
        "Name": str,
        "PositionNumber": int,
    })

schema_network_interface = Schema({
    # Optional("Name"): str, # read only
    Optional("Address"): str,
    # Optional("NodeId"): str, # read only
    # Optional("NodeType"): str, # unsupported
    Optional("UseIsoProtocol"): bool,
    Optional("MacAddress"): str,
    Optional("UseIpProtocol"): bool,
    # Optional("IpProtocolSelection"): str, # unsupported
    Optional("Address"): str,
    Optional("SubnetMask"): str,
    # Optional("UseRouter"): bool, # no need, just set RouterAddress to make this true
    Optional("RouterAddress"): str,
    Optional("DhcpClientId"): str,
    Optional("PnDeviceNameSetDirectly"): bool,
    Optional("PnDeviceNameAutoGeneration"): bool,
    Optional("PnDeviceName"): str,
    # Optional("PnDeviceNameConverted"): str, # read only
})

schema_device = {
    "p_name": str, # PLC1
    "p_typeIdentifier": str, # OrderNumber:6ES7 510-1DJ01-0AB0/V2.0
    Optional("network_interface", default={}): schema_network_interface,
    Optional("required_libraries", default=[]): list[str],
}

schema_device_plc = {
        **schema_device,
        "p_deviceName": str, # NewPlcDevice
        Optional("slots_required", default=2): int,
        Optional("Program blocks", default=[]): [Or(Schema(schema_ob_fb_fc), schema_instancedb, schema_globaldb)],
        Optional("PLC tags", default=[]): [schema_plc_tag_table],
        Optional("PLC data types", default=[]): [schema_plc_data_types],
        Optional("Local modules", default=[]): [schema_module],
    }


schema_device_ionode = {
        **schema_device,
        "p_deviceName": str, # NewPlcDevice
        Optional("slots_required", default=2): int,
        Optional("Modules", default=[]): [schema_module],
    }


schema_device_hmi = {
        **schema_device,
        Optional("HMI tags", default=[]): [schema_plc_tag_table],
    }

schema_network = Schema({
        "address": str, # 192.168.0.112
        "subnet_name": str, # Profinet
        "io_controller": str, # PNIO
    })


schema_library = Schema({
    "path": And(str, Use(Path), lambda p: Path(p)),
    Optional("read_only", default=True): bool,
    })

schema = Schema(
    {
        Optional("overwrite", default=False): bool,
        Optional("devices", default=[]): And(list, [Or(schema_device_plc, schema_device_hmi, schema_device_ionode)]),
        Optional("networks", default=[]): [schema_network],
        Optional("libraries", default=[]): [schema_library],
    },
    ignore_extra_keys=True  
)

def validate_config(data):
    return schema.validate(data)

