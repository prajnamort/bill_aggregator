# Examples

This directory contains a simple real-world example of [Bill Aggregator](../).

## Background

Jon has 3 bank accounts/cards:

- BMO Chequing Account
- BMO Credit Card
- CIBC Chequing Account

Now, he wants to do a bookkeeping for his recent transactions.

## 1. Download the bills

First, he logs in to these banks' website and downloads the transactions (in CSV format):

- [BMO_Chequing.csv](./BMO_Chequing.csv)
- [BMO_Credit.csv](./BMO_Credit.csv)
- [CIBC_Chequing.csv](./CIBC_Chequing.csv)

(For privacy reason, sensitive information in these bills have been edited.)

## 2. Edit the config

Then, he creates a config file then edits it:

```bash
cp config.example.yaml examples/config.yaml
vim examples/config.yaml
```

Since all his bank accounts exists in [config_templates](../config_templates), he just needs to copy them:

- from [config_templates/BMO_Chequing.yaml](../config_templates/BMO_Chequing.yaml) to [config.yaml](config.yaml#L5)
- from [config_templates/BMO_Credit.yaml](../config_templates/BMO_Credit.yaml) to [config.yaml](config.yaml#L19)
- from [config_templates/CIBC_Chequing.yaml](../config_templates/CIBC_Chequing.yaml) to [config.yaml](config.yaml#L34)

## 3. Run the program

All set!

Now, he runs the program:

```bash
./main.py -c examples/config.yaml -d examples/
```
