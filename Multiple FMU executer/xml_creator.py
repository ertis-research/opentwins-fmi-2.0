import xml.etree.cElementTree as ET




def create_xml(system_name, inputs, outputs, fmus, graph, final_time):
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
    elements = ET.SubElement(system, "ssd:Elements")
    
    for fmu in fmus:
        fmu_element = ET.SubElement(elements, "ssd:Component", 
                            type = "application/x-fmu-sharedlibrary",
                            source = "resources/{}.fmu".format(fmu["id"]),
                            name=fmu["id"])
        fmu_connector = ET.SubElement(fmu_element, "ssd:Connectors")

        for input in fmu["inputs"]:
            connector = ET.SubElement(fmu_connector, "ssd:Connector", 
                                    name=input["id"], kind="input")
        for output in fmu["outputs"]:
            connector = ET.SubElement(fmu_connector, "ssd:Connector", 
                                    name=output["id"], kind="output")
    # Connections of variables of the FMU
    connections = ET.SubElement(system, "ssd:Connections")

    for connection in graph:
        var_connection = ET.SubElement(connections, "ssd:Connection",
                                    startConnector = connection["from"]["var"],
                                    endConnector = connection["to"]["var"])
        if "id" in connection["from"]:
            var_connection.set("startElement", connection["from"]["id"])
        if "id" in connection["to"]:
            var_connection.set("endElement", connection["to"]["id"])
    # Final configurations
    df_experiment = ET.SubElement(root, "ssd:DefaultExperiment", 
                                stopTime=str(final_time))
    tree = ET.ElementTree(root)
    tree.write("SystemStructure.ssd", xml_declaration=True, encoding="utf-8", method="xml")
    
if __name__ == '__main__':
    fmus = [
        {
            "id": "bouncingball",
            "inputs": [
                {"id": "alturaSueloBB"}
            ],
            "outputs": [
                {"id": "alturaBolaBB"}
            ]
        },
        {
            "id": "suelo",
            "inputs": [
                {"id": "alturaSueloInicial"}
            ],
            "outputs": [
                {"id": "alturaSueloS"}
            ]
        }
    ]
    
    grafo = [
        {
            "from": {"var": "alturitaS"},
            "to": {"id": "suelo", "var": "alturaSueloInicial"}
        },
        {
            "from": {"id": "suelo", "var": "alturaSueloS"},
            "to": {"id": "bouncingball", "var": "alturaSueloBB"}
        },
        {
            "from": {"id": "bouncingball", "var": "alturaBolaBB"},
            "to": {"var": "alturitaB"}
        }
    ]
    create_xml("PruebaDriveTrain", ["alturitaS"], ["alturitaB"], fmus, grafo, 4)