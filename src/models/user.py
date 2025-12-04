class User: 
    def __init__(self, username:str):
        self.username = username
        self.items_checked_out = []
        self.items_on_hold = []
        self.checkout_history = {}
        
    def print_hold_items(self):
        if len(self.items_on_hold)==0:
            print(f"{self.username} does not currently have any books on hold.")
        else:
            counter = 0
            for book in self.items_on_hold:
                print(f"{counter}. {book}")
    
    def print_checked_out(self,user):
        if len(self.items_checked_out)==0:
            print(f"{self.username} does not currently have any books on hold")
        else: 
            counter = 0
            for book in self.items_checked_out:
                print(f"{counter}. {book}.")
                counter +=1
                
    def __str__(self):
        return self.username
    
    def __repr__(self):
        return f"username ='{self.username}',items_checked_out={self.items_checked_out},items_on_hold={self.items_on_hold}"
        
