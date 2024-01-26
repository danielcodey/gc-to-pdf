import PyPDF2
from datetime import datetime
import csv

password = "YOUR_PASSWORD_HERE"
path = "./pdf.pdf"

class GcashTransactionPDFToCSV():
    
    def check_date(self, val: str) -> bool:
        """
        Check if a field value element [0:10] is in date format
        This will serve as the signal to the loop that it is already
        the next transaction
        """
        try:
            if not (len(val) >= 10):
                return False
            datetime.strptime(val[:10], '%Y-%m-%d')
            return True
        except ValueError:
            return False
        
    def is_credit(self, transaction: list):
        """
        Credit checks if the balance is 0.00
        Note: This is still not solid as it can be possible
        that balance is 0.00 in debit
        """
        if transaction[-1] == '0.00':
            return True
        return False
        
    def separate_transactions(self, lst):
        """
        From the parsed PDF, separate each transaction
        by checking if the current field is a date
        and appends to all list
        """
        all = []
        curr = []
        for l in lst[10:]:
            if self.check_date(l):
                if curr:
                    all.append(curr)
                curr = [l]
            else:
                curr.append(l)
        return all
    
    def convert_dict_to_json(self, file_name: str, lst: list[dict]):
        """
        Converts list of dict to csv
        """
        fields = lst[0].keys()
        with open(file_name, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            writer.writerows(lst)
            
    def get_total(self, transactions: list[dict], type: str) -> int:
        """
        Get the total income or expense
        """
        if type != 'income' and type != 'expense':
            raise ValueError("Invalid type. Should only be income or expense")
        
        total = 0
        for t in transactions:
            for k,v in t.items():
                if k == type and v:
                    total += float(v)
        return round(total, 2)
    
    def set_dict(self, transactions: list):
        """
        Parse the 2D array from separate_transactions function
        and make date, transaction, income, expense and balance as keys
        
        Also append the total credit and debit and the transaction on the last
        element
        """
        lst = []
        for i, v in enumerate(transactions):
            dct = {}
            if self.is_credit(v):
                dct = {
                    "date": v[0],
                    "transaction": v[1],
                    "income": v[-2],
                    "expense": "",
                    "balance": float(v[-2]) + float(transactions[i-1][-1]) if i != 0 else v[-1]
                }
            else:
                dct = {
                    "date": v[0],
                    "transaction": v[1],
                    "income": "",
                    "expense": v[-2],
                    "balance": v[-1]
                }
            lst.append(dct)
            
        lst.append(
            {
                "date": "", 
                "transaction": "", 
                "income": self.get_total(lst, "income"), 
                "expense": self.get_total(lst, "expense"), 
                "balance": lst[-1]["balance"]
            }
        )
        return lst
    
    def main(self):
        """
        The main function
        Decrypt encrypted PDF
        Parse and convert to dict
        and generate a csv file
        """
        with open(path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            if not reader.decrypt(password):
                raise ValueError("Invalid password")
            text = ""
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text()
            transactions = self.separate_transactions(text.split('\n'))
            self.convert_dict_to_json("converted.csv", self.set_dict(transactions))
            print("Conversion Successful!")
            
GcashTransactionPDFToCSV().main()


