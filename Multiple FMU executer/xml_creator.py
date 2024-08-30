import xml.etree.cElementTree as ET




def create_xml(system_name, inputs, outputs, graph, final_time):
    # Root element
    root = ET.Element("ssd:SimpleSystemDescription", 
                    version="1.0",
                    name=system_name)

    root.set("xmlns:ssd", "http://ssp-standard.org/SSP1/SystemStructureDescription")
    root.set("xmlns:ssc", "http://ssp-standard.org/SSP1/SystemStructureCommon")
    
    # System element
    system = ET.SubElement(root, "ssd:System", 
                            name=system_name)

    # Input and output of the system
    system_connector = ET.SubElement(system, "ssd:Connectors")
    
    for input in inputs:
        connector = ET.SubElement(system_connector, "ssd:Connector", 
                                name=input, kind="input")
    for output in outputs:
        connector = ET.SubElement(system_connector, "ssd:Connector", 
                                name=output, kind="output")
        
    # Declaration of every input and output of each FMU
    
    
    # Connections of variables of the FMU


    # Final configurations
    df_experiment = ET.SubElement(root, "ssd:DefaultExperiment", 
                                stopTime=str(final_time))
    tree = ET.ElementTree(root)
    tree.write("SystemStructure.xml")
    
if __name__ == '__main__':
    create_xml("PruebaDriveTrain", ["entrada1", "entrada2"], ["salida1"], "Grafo", 4)