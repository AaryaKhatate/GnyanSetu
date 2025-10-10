# Generated manually to fix UNIQUE constraint issue

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0003_alter_usersession_session_token'),
    ]

    operations = [
        # Drop the old table
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS user_sessions;",
            reverse_sql="SELECT 1;",  # Dummy reverse
        ),
        
        # Recreate the table without UNIQUE constraint
        migrations.RunSQL(
            sql="""
                CREATE TABLE "user_sessions" (
                    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                    "session_token" varchar(255) NOT NULL,
                    "ip_address" char(39) NOT NULL,
                    "user_agent" text NOT NULL,
                    "device_info" text NOT NULL CHECK ((JSON_VALID("device_info") OR "device_info" IS NULL)),
                    "is_active" bool NOT NULL,
                    "login_time" datetime NOT NULL,
                    "logout_time" datetime NULL,
                    "last_activity" datetime NOT NULL,
                    "is_suspicious" bool NOT NULL,
                    "failed_attempts" integer unsigned NOT NULL CHECK ("failed_attempts" >= 0),
                    "user_id" char(32) NOT NULL REFERENCES "auth_user_extended" ("id") DEFERRABLE INITIALLY DEFERRED
                );
            """,
            reverse_sql="SELECT 1;",
        ),
        
        # Create index on user_id
        migrations.RunSQL(
            sql='CREATE INDEX "user_sessions_user_id_43ce9642" ON "user_sessions" ("user_id");',
            reverse_sql="SELECT 1;",
        ),
        
        # Create index on session_token (NOT UNIQUE)
        migrations.RunSQL(
            sql='CREATE INDEX "user_sessions_session_token_c02ac95f" ON "user_sessions" ("session_token");',
            reverse_sql="SELECT 1;",
        ),
    ]
