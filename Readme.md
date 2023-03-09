# Bill Aggregator

Transform and aggregate all kinds of bills into a unified, beautiful Excel Table.

- support different file formats (csv, xls)
- auto-detect file encodings (`utf-8`, `utf-16`, `gbk`, `big5`...)
- auto-detect datetime formats (`2023-02-11`, `11 FEB 2023`, `11/02/2023`, `2/11/2023`...)
- auto-detect number formats (`-$6,593.22`, `-Eu6.593,22`, `-6 593,22 грн.`, `(HK$6,593.22)`...)

For a real-world example, see [Examples](/examples).

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

Download all your bill files into a dedicated directory, like this:

```
<bills_directory>/
|- Bank_Account_1.csv
|- Bank_Account_2.csv
|- Bank_Account_3.csv
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

How to write the config?

- For well-known bank accounts, just copy config from [config_templates](/config_templates).<br>
  (If your bank account can't be found here, you are more than welcome to contribute!)
- For a detailed documentation, see [configuration.md](/configuration.md).

### 3. Run the program

Now run the program:

```bash
./main.py -c <config.yaml> -d <bills_directory>
```

The result file(s) has been put into `<bills_directory>/results/`, Enjoy your bookkeeping!
