## Generate Placeholder Data

> [!INFO]
> This script requires [Faker](https://github.com/hrishikeshio/Faker.py) to be installed. Install with `pip install faker`.

#### Entrypoint

```sh
generate-fake-toggl-data
```

### Arguments and Usage

#### Usage

```sh
usage: generate-fake-toggl-data [-h] [-s SEED] [--cache-type {sqlite,json}] cache_path
```

#### Arguments

| Short | Long           | Default | Description                                                                             |
| ----- | -------------- | ------- | --------------------------------------------------------------------------------------- |
| `-h`  | `--help`       |         | Show this help message and exit.                                                        |
| `-s`  | `--seed`       | `None`  | Set the seed value.                                                                     |
| `-t`  | `--cache-type` | `None`  | Cache storage type.<br> Required if `cache_path` doesn't end with _.json_ or _.sqlite_. |

## Clean Toggl Account

> [!WARNING]
> This will permanently delete data off a Toggl account! Be sure of what you are doing before using this script.

### Entrypoint

```sh
clean-toggl-account
```

### Arguments and Usage

#### Usage

```sh
usage: clean-toggl-account [-h] [-o {tracker,project,tag,client,org} [{tracker,project,tag,client,org} ...]]
```

#### Arguments

| Short | Long        | Default | Description                      |
| ----- | ----------- | ------- | -------------------------------- |
| `-h`  | `--help`    |         | Show this help message and exit. |
| `-o`  | `--objects` | `None`  | Which objects not to parse.      |
