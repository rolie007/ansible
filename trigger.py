import pika, subprocess
import logging, os, mysql.connector
import sys
#output to /dev/null
#old_stdout, old_stderr = sys.stdout, sys.stderr
#sys.stdout = open('/dev/null', 'w')
#sys.stderr = open('/dev/null', 'w')


# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

rabbitmq_host = '10.16.73.18'
rabbitmq_port = 5672
rabbitmq_username = 'test'
rabbitmq_password = 'test'
rabbitmq_queue = 'message_q'


def process_message(channel, method, properties, body):
    try:
        # Perform actions based on the received message
        logger.info("Received message: %r", body)
        message_body = body.decode()
        #split_list is a list of username (first) and server choice (second)
        split_list = message_body.split(',')
        userN=split_list[0]
        serV=split_list[1]
        # Get the current directory path
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Define the playbook file name
        playbook_filename = 'consume.yml'

        # Construct the full path to the playbook
        playbook_path = os.path.join(current_dir, playbook_filename)

        connection = mysql.connector.connect(
                host='10.16.73.18',
                user='root',
                password='Uamr2!!',
                database='test_db'
                                )
        # Create a cursor object to execute SQL queries
        cursor = connection.cursor()

        # Check if the account is already created on the server
        cursor.execute(f"SELECT {serV} FROM permission WHERE nuid = %s", (userN,))
        server_status = cursor.fetchone()[0]  # Fetch the value of the server column

        if server_status == "created":
            logger.info("Account already created on %s", serV)

        else:

        # Execute the playbook using the ansible-playbook command
            result = subprocess.run(['ansible-playbook', playbook_path, '--extra-vars', f'username={split_list[0]}', '--extra-vars', f'servers={split_list[1]}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)


            if result.returncode == 0:
                logger.info("Playbook execution successful")
                #run the command to vault acc in cyberark
                AccN=None
                adr =None
                if serV == "server1":
                    adr = "iamintern1.pldc.kp.org"
                    AccN = "IAM-Intern1" + userN.upper()
                if serV == "server2":
                    adr = "iamintern2.pldc.kp.org"
                    AccN = "IAM-Intern2"+ userN.upper()
                if serV == "server3":
                    adr = "iamintern3.pldc.kp.org"
                    AccN = "IAM-Intern3"+ userN.upper()

                command = (
                    f"pyark --base https://papm-dev.kp.org "
                    f"--apiuser z123456v "
                    f"--apipassword Kaiser1 "
                    f"account create "
                    f"--safe IAM-Intern "
                    f"--platformid Unix-SSH-Test "
                    f"--accountname {AccN} "
                    f"--address {adr} "
                    f"--username {userN} "
                    f"--password password"
                )
                os.system(command)

                # Define the update query
                update_query = None
                if split_list[1] == "server1":
                    update_query = "UPDATE permission SET server1 = %s WHERE nuid = %s"
                if split_list[1] == "server2":
                    update_query = "UPDATE permission SET server2 = %s WHERE nuid = %s"
                if split_list[1] == "server3":
                    update_query = "UPDATE permission SET server3 = %s WHERE nuid = %s"
                # Define the values to update
                new_column1_value = "created"
                condition_column_value = split_list[0]
                # Execute the update query
                cursor.execute(update_query, (new_column1_value, condition_column_value))
                # Commit the changes
                connection.commit()
                # Close the cursor and connection
                cursor.close()
                connection.close()




            else:
                logger.error("Playbook execution failed: %s", result.stderr)                                            
            # Acknowledge the message to remove it from the queue
        channel.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        # Handle any exceptions that occur during message processing
        logger.error("Error processing message: %s", str(e))
        # Reject the message and optionally requeue it for further processing
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

# Connect to RabbitMQ and start consuming messages
try:
    # Establish connection
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port, credentials=pika.PlainCredentials(rabbitmq_username, rabbitmq_password)))
    channel = connection.channel()

    # Declare the queue and bind to it
    channel.queue_declare(queue=rabbitmq_queue)
    channel.basic_consume(queue=rabbitmq_queue, on_message_callback=process_message)

    # Start consuming messages
    logger.info("Consumer started. Waiting for messages...")
    channel.start_consuming()

except Exception as e:
    # Handle any exceptions that occur during script execution
    logger.error("An error occurred: %s", str(e))
