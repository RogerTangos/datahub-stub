from django.core.management.base import BaseCommand

from config import settings
from core.db.manager import DataHubManager


class Command(BaseCommand):
    help = ("If a user has inserted data into their public repo, "
            "This migrates that data to a different repo for them")

    def handle(self, *args, **options):
        migrate_tables_and_views(None, None)


def migrate_tables_and_views(apps, schema_editor):
    print("\n\n********* Beginning migrate_tables_and_views *********")
    DataHubManager.execute_sql

    all_users = DataHubManager.list_all_users()
    print("all_users before filter")
    print(all_users)
    # filter out the anonymous user, which doesn't have a db
    all_users = [username for username in all_users if (
        username != settings.ANONYMOUS_ROLE)
    ]
    print("all_users after filter")
    print (all_users)

    # give users select/update/insert access to their rows in the  policy table
    for username in all_users:
        print("current user")
        print(username)
        with DataHubManager(username) as m:
            res = m.execute_sql(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public'")
            print(res)
            tables_and_views = [table[0] for table in res['tuples']]

        move_tables_to_new_schema(username, tables_and_views)


def move_tables_to_new_schema(username, tables_and_views):
    # if they do have tables/views
    if len(tables_and_views) > 0:
        repo_name = create_and_return_name_for_public_schema(username)

        for table in tables_and_views:
            with DataHubManager(username) as m:
                query = ('Alter table public.%s '
                         'set schema %s') % (table, repo_name)
                m.execute_sql(query)


def create_and_return_name_for_public_schema(username):
    with DataHubManager(username) as m:
        repos = m.list_repos()

        new_name = 'migrated_public_repos'

        if new_name in repos:
            new_name = 'migrated_public_repos_1'

        counter = 1
        while new_name in repos:
            counter += 1
            new_name = new_name[0:len(new_name) - 2] + str(counter)

        m.create_repo(new_name)
    return new_name
