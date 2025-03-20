import boto3
import uuid

def create_inference_profile(
    region='ap-northeast-1',
    model_id='anthropic.claude-3-sonnet-20240229-v1:0',
    profile_name='my-inference-profile',
    memory_size_in_gb=None,
    provisioned_concurrency=None,
    max_model_concurrency=None,
    container_environment_variables=None
):
    """
    Creates an application inference profile for the specified model in Amazon Bedrock.

    Parameters:
    - region (str): The region where the inference profile will be created. Default is 'ap-northeast-1'.
    - model_id (str): The ID of the model for which the inference profile is created.
    - profile_name (str): The name of the inference profile.
    - memory_size_in_gb (int, optional): The memory size in GB for the inference profile.
    - provisioned_concurrency (int, optional): The number of provisioned concurrent executions.
    - max_model_concurrency (int, optional): The maximum number of concurrent model executions.
    - container_environment_variables (dict, optional): Environment variables for the container.

    Returns:
    - str: The ARN of the created inference profile if successful, otherwise None.
    """
    # Create a Bedrock client
    bedrock = boto3.client('bedrock', region_name=region)

    # Construct the model ARN
    model_arn = f'arn:aws:bedrock:{region}::foundation-model/{model_id}'

    # Generate a unique client request token
    client_request_token = str(uuid.uuid4())

    # Define the model source for the inference profile
    model_source = {'copyFrom': model_arn}

    # Prepare the request parameters
    request_params = {
        'clientRequestToken': client_request_token,
        'description': f'Inference profile for {model_id}',
        'inferenceProfileName': profile_name,
        'modelSource': model_source
    }

    # Add optional parameters if provided
    if memory_size_in_gb is not None:
        request_params['memoryInGb'] = memory_size_in_gb

    if provisioned_concurrency is not None:
        request_params['provisionedConcurrency'] = provisioned_concurrency

    if max_model_concurrency is not None:
        request_params['maxModelConcurrency'] = max_model_concurrency

    if container_environment_variables is not None:
        request_params['containerEnvironmentVariables'] = container_environment_variables

    try:
        # Create the inference profile
        response = bedrock.create_inference_profile(**request_params)

        # Print success message and ARN
        print("Inference profile created successfully.")
        print("ARN:", response['inferenceProfileArn'])

        return response['inferenceProfileArn']
    except Exception as e:
        # Handle any exceptions
        print("Error creating inference profile:", str(e))
        return None

# Example usage with additional parameters
if __name__ == "__main__":
    inference_profile_arn = create_inference_profile(
        profile_name="example-profile",
        memory_size_in_gb=4,
        provisioned_concurrency=2,
        max_model_concurrency=5,
        container_environment_variables={
            "TIMEOUT": "300",
            "MAX_TOKENS": "2000"
        }
    )
    print("Inference profile ARN:", inference_profile_arn)