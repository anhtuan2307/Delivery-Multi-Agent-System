# package.py

class Package:
    
    def __init__(self, package_id: int, dropoff_location: int, pickup_location: int):
        self.id = package_id
        self.pickup_location = pickup_location
        self.dropoff_location = dropoff_location
        self.status = 'pending'  
        self.assigned_agent = None 

    def assign(self, agent):
        self.status = 'assigned'
        self.assigned_agent = agent.id 
        print(f"[Package {self.id}] Assigned to Agent {agent.id}.")

    def complete(self):
        self.status = 'delivered'
        print(f"[Package {self.id}] Delivered.")

    def __repr__(self):
        return f"Package(ID={self.id}, Status='{self.status}', Agent={self.assigned_agent})"