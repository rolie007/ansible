import mysql.connector
import time
import subprocess
import os

# Database configuration
db_config = {
    'host': '10.16.73.18',
    'user': 'root',
    'password': 'Uamr2!!',
    'database': 'test_db'
}
#username = 'roland'
#server = 'server1'
def cleanup(username, server):
    # Perform cleanup tasks here
    # You can add the logic to delete the user account, revoke sudo privileges, etc.
    print(f"Cleaning up '{username}' on '{server}'")
    try:
        accN = None
        if server == "server1":
            accN= "IAM-Intern1"+username.upper()
        if server == "server2":
            accN= "IAM-Intern2"+username.upper()
        if server == "server3":
            accN= "IAM-Intern3"+username.upper()
        command = (
                f"pyark --base https://papm-dev.kp.org "
                f"--apiuser z123456v "
                f"--apipassword Kaiser1 "
                f"account delete "
                f"--safe IAM-Intern "
                f"--accountname {username} "
                f"--keywords {accN} "
            )

        os.system(command)
        # Get the current directory path
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Define the playbook file name
        playbook_filename = 'clean_up.yml'

        # Construct the full path to the playbook
        playbook_path = os.path.join(current_dir, playbook_filename)


        # Execute the playbook using the ansible-playbook command
        result = subprocess.run(['ansible-playbook', playbook_path, '--extra-vars', f'userN={username}', '--extra-vars', f'servers={server}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        # Update the database table to set the server column to 'NA'
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        print(f"Resetting {server} column")
        update_query = f"UPDATE permission SET {server} = 'NA' WHERE nuid = %s"
        cursor.execute(update_query, (username,))
        connection.commit()

        cursor.close()
        connection.close()
    except Exception as e:
        print(f"An error occurred while updating the database: {str(e)}")




def main():
   # cleanup(username, server)
    while True:
        try:
            # Connect to the MariaDB server
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor()

            # Query the database for rows with server status set to 'deprovisioned'
            query = "SELECT nuid, server1, server2, server3 FROM permission WHERE server1 = 'closing' OR server2 = 'closing' OR server3 = 'closing'"
            cursor.execute(query)
            rows = cursor.fetchall()

            if not rows:
                print("Nothing to cleanup")
            else:
                for row in rows:
                    username = row[0]
                    servers = ['server1', 'server2', 'server3']

                    # Iterate through server columns to find the deprovisioned server
                    for server in servers:
                        if row[servers.index(server) + 1] == 'closing':
                            cleanup(username, server)
            #Close cursor and connection
            cursor.close()
            connection.close()

        except Exception as e:
            print(f"An error occurred: {str(e)}")

        # Sleep for 1 minute before checking again
        time.sleep(60)

if __name__ == "__main__":
    main()
