import os
import json
import copy

class TitleSolver():
    def __init__(self):
        pass

    def get_newnode(self, title_id, title_text):
        """get a new node for title
        """
        new_node = {"node_type": 0, "id": title_id, "level":1 , "text": title_text, "children": []}
        return new_node

    def get_newentry(self, title_id, page, box, content):
        """get a new entry for title
        """
        new_entry = [title_id, page, box, content]
        return new_entry

    def get_columns(self):
        """get columns for metacsv
        """
        columns = ["id", "page", "position", "text"]
        return columns
    
class TextSolver():
    def __init__(self):
        pass

    def get_newnode(self, text_id):
        """get a new node for text
        """
        new_node = {"node_type": 1, "id": text_id}
        return new_node

    def get_newentry(self, text_id, page, box, content):
        """get a new entry for text
        """
        new_entry = [text_id, page, box, content]
        return new_entry
    
    def get_columns(self):
        """get columns for metacsv
        """
        columns = ["id", "page", "position", "text"]
        return columns
    
class ListSolver():
    def __init__(self):
        pass

    def get_newnode(self, list_id):
        """get a new node for list
        """
        new_node = {"node_type": 2, "id": list_id }
        return new_node

    def get_newentry(self, list_id, page, box, content):
        """get a new entry for list
        """
        new_entry = [list_id, page, box, content]
        return new_entry
    
    def get_columns(self):
        """get columns for metacsv
        """
        columns = ["id", "page", "position", "text"]
        return columns
        
class TableSolver():
    def __init__(self):
        pass

    def get_newnode(self, table_id):
        """get a new node for table
        """
        new_node = {"node_type": 3, "id": table_id}
        return new_node

    def get_newentry(self, table_id, page, box, content):
        """get a new entry for table
        """
        new_entry = [table_id, page, box, content]
        return new_entry

    def get_columns(self):
        """get columns for metacsv
        """
        columns = ["id", "page", "position", "text"]
        return columns

class FigureSolver():
    def __init__(self):
        pass

    def get_newnode(self, figure_id):
        """get a new node for figure
        """
        new_node = {"node_type": 4, "id": figure_id}
        return new_node

    def get_newentry(self, figure_id, page, box, content):
        """get a new entry for figure
        """
        new_entry = [figure_id, page, box, content]
        return new_entry
    
    def get_columns(self):
        """get columns for metacsv
        """
        columns = ["id", "page", "position", "text"]
        return columns