CP-BackupTool
=============

backup and restore tool for CouchPotato's wanted list.

After cloning this repo you need to edit the couch.cfg to add your correct host, path and apikey (from CouchPotato, settings, general)
You can also specify the path to a CFG file:
```
./wanted.py --type backup --cfg /your/path/cfg --file /volume1/Public/backup.txt
```
Also, you can use your settings.conf from couchpotato:
```
./wanted.py --type backup --cfg /your/path/.couchpotato/settings.conf --file /volume1/Public/backup.txt
```

###### Backup
To create a backup of your wanted movies, run the script passing in the options "backup" and the full path/name of the backup file you want to create
```
./wanted.py --type backup --file /volume1/Public/backup.txt
```

###### Restore
Now, should your database need to be deleted, or is otherwise lost, run this script with the option "restore" followed by the path to the backup file.
(NOTE: If you did a complete re-install, you will need to enter the NEW api key in the couch.cfg)
```
./wanted.py --type restore --file /volume1/Public/backup.txt
```

It will restore the qualities, but if you reinstalled couchpotato only the default qualities will exist.
If this is the case you'll need to recreate those and manually edit these in the wanted list.
In case you worry about auto-snatch with the wrong quality etc (not default) I suggest setting your downloader to "manual" to prevent auto-snatching, before running the restore. Take the downloader out of "manual" mode once you are comfortable all has been restored correctly.

###### Clear
This will delete all movies in your managed list.
```
./wanted.py --type clear
```

###### Delete
This will delete all movies in your wanted list.
```
./wanted.py --type delete
```

###### Export
To create a backup of your existing library of movie files, run the script passing in the options "export" and the full path/name of the backup file you want to create
```
./wanted.py --type export --file /volume1/Public/export.txt
```

###### More options
To see all options for wanted.py:
```
./wanted.py -h
```
