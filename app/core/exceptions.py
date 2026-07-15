






class CustomException(Exception):
    def __init__(self,detail:str,status_code:int = 400):
        self.detail = detail
        self.status_code = status_code
    
class NotFoundException(CustomException):
    def __init__(self,detail:str="Resource not found"):
        super().__init__(detail=detail,status_code=404)

