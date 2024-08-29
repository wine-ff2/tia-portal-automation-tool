from lib.pp import pp
from gui import MenuBar, FileDialog, Notebook
import wx


class MainWindow(wx.Frame):
    def __init__(self, parent, title) -> None:
        wx.Frame.__init__(self, parent, title=title, size=(800,600))
        self.config: pp.objects.Config = None

        self.CreateStatusBar()

        menubar = MenuBar.new(self)
        notebook = Notebook.new(self)
        self.tab_conf_textbox = notebook.tab_project.config_path

        self.SetMinSize((600,480))

        self.Show(True)


    def OnOpen(self, e):
        filepath = FileDialog.open_config(self)
        if not filepath:
            return

        self.tab_conf_textbox.write(filepath)
        try:
            self.config = pp.parse(filepath)
            pp.tia, pp.comp, pp.hwf = pp.import_siemens_module(self.config.dll)
            # self.splitter.tree.populate(self.portal.config)

        except IOError:
            wx.LogError("Cannot open file '%s'." % newfile)

    def OnClose(self, e):
        pp.tia = None
        pp.comp = None
        pp.hwf = None
        self.config = None

    def OnRun(self, e):
        if pp.tia == None or pp.comp == None or pp.hwf == None:
            return

        config: Config = self.config

        portal = pp.TiaPortal(config)
        project = pp.create_project(portal, config.project.name, config.project.directory)

        devices: list[Siemens.Engineering.HW.Device] = []
        interfaces: list[Siemens.Engineering.HW.Features.NetworkInterface] = []
        for data in config.project.devices:
            device_composition: Siemens.Engineering.HW.DeviceComposition = project.Devices
            device: Siemens.Engineering.HW.Device = pp.create_device(device_composition, data)
            devices.append(device)
            hw_object: Siemens.Engineering.HW.HardwareObject = device.DeviceItems[0]
            for data_dev_item in data.items:
                pp.create_and_plug_device_item(hw_object, data_dev_item, data.slots_required)
            device_items = pp.access_device_item_from_device(device, 1).DeviceItems
            for item in device_items:
                network_service = pp.access_network_interface_feature(item)
                if type(network_service) is pp.hwf.NetworkInterface:
                    node: Siemens.Engineeering.HW.Node = network_service.Nodes[0]
                    attributes = {"Address" : data.network_address}
                    pp.set_object_attributes(node, **attributes)
                    print(f"Added a network address: {data.network_address}")
                    interfaces.append(network_service)

            for device_item in device.DeviceItems:
                software_container: Siemens.Engineering.HW.Features.SoftwareContainer = pp.access_software_container(device_item)
                if not software_container:
                    continue
                software_base: Siemens.Engineering.HW.Software = software_container.Software
                if not isinstance(software_base, pp.tia.SW.PlcSoftware):
                    continue
                tag_table = pp.create_tag_table(software_base, data.tag_table)
                if not isinstance(tag_table, pp.tia.SW.Tags.PlcTagTable):
                    continue
                for tag in data.tag_table.tags:
                    pp.create_tag(tag_table, tag)

        subnet: Siemens.Engineering.HW.Subnet = None
        io_system: Siemens.Engineering.HW.IoSystem = None
        network: list[pp.objects.Network] = config.project.networks

        for i in range(len(network)):
            for n in range(len(interfaces)):
                if interfaces[n].Nodes[0].GetAttribute('Address') != network[i].address:
                    continue
                if i == 0:
                    subnet, io_system = pp.create_io_system(interfaces[0], network[0])
                    print(f"Creating Subnet and IO system: {network[0].subnet_name} <{network[0].io_controller}>")
                    continue
                pp.connect_to_io_system(interfaces[n], subnet, io_system)
                print(f"Connecting to Subnet and IO system: {network[i].subnet_name} <{network[i].io_controller}>")

        
        # Add PLC Blocks from imported Master Copy Library
        for library in config.project.libraries:
            print(f"Opening library: {library.path}")
            lib = pp.open_library(portal, pp.FileInfo(library.path.as_posix()), library.read_only)
          
            for master_copy in library.master_copies:
                print(f"Adding {master_copy.source} to {master_copy.destination}...")
                source = pp.find_master_copy_by_name(lib, master_copy.source)

                plc = pp.find_plc_by_name(project, master_copy.destination)
                if not plc:
                    continue
                block = plc.BlockGroup.Blocks
                copy = pp.create_plc_block_from_mastercopy(block, source)
                attrs = {"Name": master_copy.name}
                pp.set_object_attributes(copy, **attrs)

                if copy:
                    print(f"Copied PLC block: {copy.Name}")

            fbs: list[str] = []
            dbs: list[str] = []
            for instance in library.instances:
                source = pp.find_master_copy_by_name(lib, instance.source)
                plc = pp.find_plc_by_name(project, instance.destination)
                if not plc:
                    continue

                block = plc.BlockGroup.Blocks
                fb = pp.create_plc_block_from_mastercopy(block, source)
                attrs = {"Name": instance.name}
                pp.set_object_attributes(fb, **attrs)
                db = pp.create_instance_db(plc, instance.name, 1, instance.name)

                fbs.append(instance.name)
                dbs.append(db.Name)

            xml = pp.OB.generate("Main", 1, "LAD", fbs, dbs)


    def OnExit(self, e):
        self.Close(True)
        self.Destroy()
    

if __name__ == '__main__':
    app = wx.App(False)
    frame = MainWindow(None, title="TIA Portal Automation Tool")
    app.MainLoop()

