# Bill Aggregator

Bill Aggregator is a program that simplifies your personal/family bookkeeping.

It aggregates all your bills from different formats/schemas into a single, unified file.

Supported bill file formats:

- csv
- xls

Supported export file formats:

- xlsx (Excel 2007+)

## Installation

Clone this repository:

```bash
git clone https://github.com/prajnamort/bill_aggregator.git
```

Install dependencies (you need have [python3](https://www.python.org/downloads/) and [pip3](https://pip.pypa.io/en/stable/installation/) installed):

```bash
cd bill_aggregator/
pip3 install -r requirements.txt
```

## Usage

### 1. Download your bills

Put all your bill files into a dedicated directory, like this:

```
<bills_directory>/
|- Bank_Account_1.csv
|- Bank_Account_2.csv
|- Bank_Account_3.csv
|- Credit_Card_1.csv
|- Credit_Card_2.csv
|- Paypal.csv
|- ...
```

### 2. Edit the config

Create a new config file (only for the first time):

```bash
cp config.example.yaml config.yaml
```

Edit the config file:

```bash
<editor> config.yaml
```

### 3. Run the program

Now run the program:

```bash
./main.py -c <config.yaml> -d <bills_directory>
```

The result file(s) has been put into `<bills_directory>/results/`, Enjoy your bookkeeping!
