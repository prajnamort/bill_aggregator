# Configuration

This is a detailed explaination of `config.yaml` for [Bill Aggregator](/../../).

At the highest level, your `config.yaml` looks like this:

```yaml
# configs for reading bill files
bill_groups: [...]

# configs for exporting results
export_to: xlsx
export_config: {...}
```

It contains two main sections:

1. configs for reading bill files
2. configs for exporting results

## Configs for reading bill files

Configs in this section tells the program:

- Which bill file(s) is for each account?
- Where is the data located in the bill file(s)?

With the first question, comes the notion of "Bill Group".

### What is a "Bill Group"?

After you download all your bills, it might look like this:

```
<bills_directory>/
|- XX_Account.csv
|- YY_Account_Jan.csv
|- YY_Account_Feb.csv
```

Although you have 3 "Bill Files", there's only 2 "Bill Groups" here: `XX_Account` and `YY_Account`.

Since `YY_Account_Jan.csv` and `YY_Account_Feb.csv` come from the same account, and they use exactly the same formats,
you don't want their configs to be different.

So in your `config.yaml`, you can see "Bill Group" is the basic unit of our config (it represents one or more bill files):

```yaml
# configs for reading bill files
bill_groups:
  # Bill Group 1
  - ...

  # Bill Group 2
  - ...

  # Bill Group 3
  - ...
```

### How to write config for each "Bill Group"?

TODO...
