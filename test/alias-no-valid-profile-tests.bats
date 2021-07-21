#!/usr/bin/env bats

# Copy the aliases file to the local ~/.aws/cli directory so it becomes operative
cp ../alias ~/.aws/cli/alias

unset AWS_DEFAULT_PROFILE
unset AWS_PROFILE

# Localstack endpoint
# https://pythonawesome.com/localstack-a-fully-functional-local-aws-cloud-stack/
# --endpoint-url http://localhost:4566 --region us-east-1


#tostring
@test "Checking tostring" {
  run aws tostring tostring.json
  [ "$status" -eq 0 ]
  echo line0: "${lines[0]}"
  [ "${lines[0]}" = '"{\"StreamNames\":[]}"' ]
}

#region
@test "Checking region" {
  run aws region us-east-1
  [ "$status" -eq 0 ]
}

#profiles
@test "Checking profiles" {
  run aws profiles
  [ "$status" -eq 0 ]
  [ "${lines[0]}" = "export AWS_DEFAULT_PROFILE= to set a default profile." ]
 }

# update-aliases
@test "Checking update-aliases" {
  run aws update-aliases
  [ "$status" -eq 0 ]
  [ "${lines[0]}" = "Downloaded https://raw.githubusercontent.com/msaum/aws-alias/master/alias" ]
 }

#upgrade
@test "Checking upgrade" {
  skip
  run aws upgrade
  [ "$status" -eq 0 ]
 }

#install
@test "Checking install" {
  skip
  run aws install
  [ "$status" -eq 0 ]
}

#rotate-iam-keys
# Currently just testing failure states
# The function itself gets exercised.  Hard to simulate rotating a perm key.
@test "Checking rotate-iam-keys" {
  unset PROFILE
  run aws rotate-iam-keys
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "Your long term credentials must be provided as an argument." ]

  export AWS_DEFAULT_PROFILE=not-a-valid-aws-profile-name
  run aws rotate-iam-keys not-a-valid-aws-profile-name
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "Rotating keys for profiles: not-a-valid-aws-profile-name" ]
}

#iam-keys-days-remaining
# Currently just testing failure states
# The function itself gets exercised.  Hard to simulate checking this.
@test "Checking iam-keys-days-remaining" {
  run aws iam-keys-days-remaining
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "Can't determine your AWS Profile. Set AWS_PROFILE, or AWS_DEFAULT_PROFILE" ]
}

#mfa
# Currently just testing failure states
# The function itself gets exercised.  Hard to simulate checking this.
@test "Checking mfa" {
  run aws mfa
  [ "$status" -eq 1 ]
}

#whoami
# Currently just testing failure states
# The function itself gets exercised.  Hard to simulate checking this.
@test "Checking whoami" {
  run aws whoami
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}

##create-assume-role
## Currently just testing failure states
## The function itself gets exercised.  Hard to simulate checking this.
# Usage: aws create-assume-role <rolename> <service>
@test "Checking create-assume-role" {
  run aws create-assume-role
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Missing an argument" ]

  run aws create-assume-role my-fake-test-role
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Missing an argument" ]

  run aws create-assume-role my-fake-test-role my-fake-service
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}


#find-access-key
# Usage: aws find-access-key <access key>
@test "Checking find-access-key" {
  run aws find-access-key myaccesskey
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}

#list-iam-users
@test "Checking list-iam-users" {
  run aws list-iam-users
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}

#list-user-keys
# Usage: aws list-user-keys <username>
@test "Checking list-user-keys" {
  # Send a bad argument to a bad profile
  run aws list-user-keys myfakeusername
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]

  run aws list-user-keys
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]

}

#list-virtual-mfa
# Usage: aws list-virtual-mfa <username>
@test "Checking list-virtual-mfa" {
  run aws list-virtual-mfa myfakeusername
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}

#delete-virtual-mfa
# Usage: aws delete-virtual-mfa <username>
@test "Checking delete-virtual-mfa" {
  run aws delete-virtual-mfa myfakeusername
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]

  run aws delete-virtual-mfa
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Missing an argument" ]
}

#find-users-without-mfa
# Usage: aws find-users-without-mfa
@test "Checking find-users-without-mfa" {
  run aws find-users-without-mfa
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}

#generate-sts-token
# Usage: aws generate-sts-token
@test "Checking generate-sts-token" {
  run aws generate-sts-token
  echo status: $status
  echo lines[0]: "${lines[0]}"
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}

#assume
# Usage: aws assume <role-arn>
@test "Checking assume" {
  run aws assume
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Missing an argument" ]

  run aws assume my-fake-arn-name
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}

#running-instances
@test "Checking running-instances" {
  run aws running-instances
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}

#ebs-volumes
@test "Checking ebs-volumes" {
  run aws ebs-volumes
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}

#amazon-linux-amis
@test "Checking amazon-linux-amis" {
  run aws amazon-linux-amis
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}

#list-sgs
@test "Checking list-sgs" {
  run aws list-sgs
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}

#sg-rules
#Usage: aws sg-rules <security group id>
@test "Checking sg-rules" {
  run aws sg-rules
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Missing an argument" ]

  run aws sg-rules my-fake-security-group-id
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}

#get-group-id
# Usage: aws get-group-id <security group name>
@test "Checking get-group-id" {
  run aws get-group-id
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Missing an argument" ]

  run aws get-group-id my-fake-security-group-name
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}

#authorize-my-ip-by-name
@test "Checking authorize-my-ip-by-name" {
  run aws authorize-my-ip-by-name
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Missing an argument" ]

  run aws authorize-my-ip-by-name my-fake-security-group-name
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}

#public-ports
@test "Checking public-ports" {
  run aws public-ports
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}

#myip
@test "Checking myip" {
  run aws myip
  echo status: $status
  # AWS returns a 252 even when it is successful.  I assume this is because we don't actually run an AWS command.
  [ "$status" -eq 252 ]
}

#allow-my-ip
# Usage: aws allow-my-ip <security group name>
@test "Checking allow-my-ip" {
  run aws allow-my-ip
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Missing an argument" ]

  run aws allow-my-ip my-fake-security-group-name
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}

# revoke-my-ip
# Usage: revoke-my-ip <security group name> <protocol> <port>
@test "Checking revoke-my-ip" {
  run aws revoke-my-ip
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Missing an argument" ]

  run aws revoke-my-ip my-fake-security-group-name
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Missing an argument" ]

  run aws revoke-my-ip my-fake-security-group-name my-fake-protocol
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Missing an argument" ]

  run aws revoke-my-ip my-fake-security-group-name my-fake-protocol my-fake-port
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}

# allow-my-ip-all
# Usage: aws allow-my-ip-all <security group name>
@test "Checking allow-my-ip-all" {
  run aws allow-my-ip-all
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Missing an argument" ]

  run aws allow-my-ip-all my-fake-security-group-name
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}

#revoke-my-ip-all
# Usage: aws revoke-my-ip-all <security group name>
@test "Checking allow-my-ip-all" {
  run aws revoke-my-ip-all
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Missing an argument" ]

  run aws revoke-my-ip-all my-fake-security-group-name
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}
#delete-ami
# Usage: aws delete-ami <AMI ID>
@test "Checking delete-ami" {
  run aws delete-ami
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Missing an argument" ]

  run aws delete-ami my-fake-ami-id
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}

#list-instances
# Usage: aws list-instances <region>
@test "Checking list-instances" {
  run aws list-instances
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Missing an argument" ]

  run aws list-instances my-fake-region-id
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}

#connect-ssh
# Usage: aws connect-ssh <instance-id>
@test "Checking connect-ssh" {
  skip
  run aws connect-ssh
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Missing an argument" ]

  run aws connect-ssh my-fake-instance-id
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}

#search-instances
# Usage: aws search-instances <name>
@test "Checking search-instances" {
  run aws search-instances
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Missing an argument" ]

  run aws search-instances my-fake-name
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}

#list-all-regions
# Usage: aws list-all-regions
@test "Checking list-all-regions" {
  run aws list-all-regions
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}

#list-azs
# Usage: aws list-azs
@test "Checking list-azs" {
  run aws list-azs
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}

# vpc-peers
# Usage: aws vpc-peers
@test "Checking vpc-peers" {
  run aws vpc-peers
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}

# find-instances-in-sg
# aws find-instances-in-sg <network interface group name> <security group id>
@test "Checking find-instances-in-sg" {
  run aws find-instances-in-sg
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Missing an argument" ]

  run aws find-instances-in-sg my-fake-network-interface-group-name
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Missing an argument" ]

  run aws find-instances-in-sg my-fake-network-interface-group-name my-fake-security-group-id
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}

#find-ssh-open
# Usage: aws find-ssh-open
@test "Checking find-ssh-open" {
  run aws find-ssh-open
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}

#get-asg-instance-ips
# Usage: aws get-asg-instance-ips <ASG Name>
@test "Checking get-asg-instance-ips" {
  run aws get-asg-instance-ips
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Missing an argument" ]

  run aws get-asg-instance-ips my-fake-asg-name
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}

# find-host-by-instance-id
# Usage: aws find-host-by-instance-id <instance ID>
@test "Checking find-host-by-instance-id" {
  run aws find-host-by-instance-id
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Missing an argument" ]

  run aws find-host-by-instance-id my-fake-instance-id
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}

#find-instance-by-public-ip
# Usage: aws find-instance-by-public-ip <public ip>
@test "Checking find-instance-by-public-ip" {
  run aws find-instance-by-public-ip
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Missing an argument" ]

  run aws find-instance-by-public-ip my-fake-ip-address
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}

#find-nat-gateway-by-public-ip
# Usage: aws find-nat-gateway-by-public-ip <public ip>
@test "Checking find-instance-by-public-ip" {
  run aws find-nat-gateway-by-public-ip
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Missing an argument" ]

  run aws find-nat-gateway-by-public-ip my-fake-ip-address
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
}

#list-igw
@test "Checking list-igw" {
  skip
  }

#list-ngw
@test "Checking list-ngw" {
  skip
  }

#list-vgw
@test "Checking list-vgw" {
  skip
  }

#list-vpn-connection
@test "Checking list-vpn-connection" {
  skip
  }

#list-instance-status
@test "Checking list-instance-status" {
  skip
  }

#list-vpcs
@test "Checking list-vpcs" {
  skip
  }

#list-subnets
@test "Checking list-subnets" {
  skip
  }

#list-routes
@test "Checking list-routes" {
  skip
  }

#get-dns-from-instance-id
@test "Checking get-dns-from-instance-id" {
  skip
  }

#get-instance-id-from-dns
# Usage: aws get-instance-id-from-dns <dns name>
@test "Checking get-instance-id-from-dns" {
  skip
  run get-instance-id-from-dns
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Missing an argument" ]

  run aws get-instance-id-from-dns my-fake-dns-name
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
  }

#log-groups
@test "Checking log-groups" {
  run aws log-groups
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
  }

#last-log
# Usage: aws last-log
@test "Checking last-log" {
  run aws last-log
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Missing an argument" ]

  run aws last-log my-fake-log-group
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
  }

#docker-ecr-login
@test "Checking docker-ecr-login" {
  run aws docker-ecr-login
  echo status: $status
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "ERROR: Unable to determine your AWS user credentials.  Check your AWS credentials configuration." ]
  }

