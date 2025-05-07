from correctionlib.schemav2 import Variable, Correction, Category, Binning
import json

class CorrectionWriter:
    def __init__(self, schema_version: int = 2):
        self.corrections = {}
        self.schema_version = schema_version


    """
        Add a correction to the list of corrections.
        :param name: Name of the correction
        :param correction: Correction object
        :return: None
    """
    def add_correction(self, name: str, correction: Correction):
        self.corrections[name] = correction


    """
        Make a category correction.
        :param name: Name of the correction
        :param data: Data of the correction
        :param edges: Edges of the correction
        :return: Category object
    """
    def __make_category(self, name, data, edges):
        content = []
        for i in range(len(edges)):
            content.append({
                "key": edges[i],
                "value": data[i]
            })
        return Category(
            nodetype="category",
            input=name,
            content=content
        )

    """
        Make a binned correction.
        :param name: Name of the correction
        :param content: Content of the correction
        :param edges: Edges of the correction
        :param flow: Flow type, either "error" or "overflow"
        :return: Binning object
    """
    def __make_binning(self, name, content, edges, flow):
        return Binning(
            nodetype="binning",
            input=name,
            edges=edges,
            content=content,
            flow=flow
        )


    """
        Check if the edges are categories.
        If the first element of the edges is a string, it returns True.
    """
    def __is_category(self, edges):
        if isinstance(edges[0], str):
            return True
        else:
            return False
        

    """
        Recursive function to build the nodes of the correction tree.
        If the edges are strings it is handled as a category, otherwise as a binned correction.
    """
    def __build_nodes(self, inputs, edges, data, flow, idx = 0):
        name = inputs[idx]["name"]
        edges_ = edges[idx]

        if idx+1 == len(inputs):
            if self.__is_category(edges_):
                return self.__make_category(name, data, edges_)
            else :
                return self.__make_binning(name, data, edges_, flow)
        
        content = []
        if self.__is_category(edges_):
            n_edges = len(edges_)
        else:
            n_edges = len(edges_)-1
        for i in range(n_edges):
            subnode = self.__build_nodes(inputs, edges, data[i], flow, idx+1)
            content.append(subnode)
        
        if self.__is_category(edges_):
            return self.__make_category(name, content, edges_)
        else:
            return self.__make_binning(name, content, edges_, flow)

    """
        Add a N-dimensional binned corrections with variation categories to the list of corrections.

        :param name: Name of the correction
        :param description: Description of the correction
        :param version: Version of the correction
        :param inputs: List of input variables, eg: [{"name": "pt", "type": "real", "description": "Probe pt"}]
        :param output: Output variable, eg: {"name": "sf", "type": "real", "description": "Scale factor"}
        :param edges: List of edges for each input variable, eg: [[0, 10, 20], [0, 1, 2]]
        :param data: List of data for each bin, eg: [[1.0, 1.1], [1.2, 1.3]]
        :param flow: Flow type, either "error" or "overflow". Set to "error" by default.
        :return: None
    """
    def add_multibinned_correction(
        self,
        name: str,
        description: str,
        version: int,
        inputs: list,
        output: dict,
        edges: list,
        data: list, 
        flow: str = "error"
    ):

        content = self.__build_nodes(inputs, edges, data, flow)

        correction = Correction(
            name=name,
            description=description,
            version=version,
            inputs=[Variable.parse_obj(v) for v in inputs],
            output=Variable.parse_obj(output),
            data=content
        )
       
        self.corrections[name] = correction

    """
        Assemble into a dict ready for json.dump(...)
        Excluding None values
    """
    def __to_json_dict(self):
        return {
            "schema_version": self.schema_version,
            "corrections": [c.model_dump(exclude_none=True) for c in self.corrections.values()]
        }


    """
        Save the correction to a json file.
        :param filename: Name of the file to save
        :return: None
    """
    def save_json(self, filename: str):
        print("Saving correction json to:", filename)
        with open(filename, "w") as f:
            json.dump(self.__to_json_dict(), f, indent=4)

