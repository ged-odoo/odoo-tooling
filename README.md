# odoo-tooling

Some tooling to work on odoo, as a dev

Probably still very dependant on my specific config, but this tool may become more configurable in the future

## Examples

```bash
# list all currently checked-out branch (community/enterprise)
./start-odoo.py -l

# drop testdb, then start odoo server with enterprise addons, and give -i crm to server
./start-odoo.py -d --enterprise -- -i crm

# start web test suite in command line
./start-odoo.py --test-web
```