from aws_cdk import (
    App, Stack,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
    CfnOutput, CfnParameter
)
from constructs import Construct

class AlbCdkStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        instance_type = CfnParameter(self, "InstanceType",
                                      type="String",
                                      allowed_values=["t2.micro", "t2.small"],
                                      description="EC2 instance type")
        key_pair_name = CfnParameter(self, "KeyPair",
                                     type="String",
                                     description="EC2 Key Pair")
        your_ip = CfnParameter(self, "YourIp",
                               type="String",
                               description="Your IP in CIDR notation")

        vpc = ec2.Vpc(self, "EngineeringVpc",
                      ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/18"),
                      subnet_configuration=[
                          ec2.SubnetConfiguration(name="PublicSubnet",
                                                  subnet_type=ec2.SubnetType.PUBLIC,
                                                  cidr_mask=24)
                      ])

        sg = ec2.SecurityGroup(self, "WebserversSG",
                               vpc=vpc,
                               description="Allow ssh and http",
                               allow_all_outbound=True)
        sg.add_ingress_rule(ec2.Peer.ipv4(your_ip.value_as_string), ec2.Port.tcp(22), "SSH Access")
        sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "HTTP Access")

        ami_linux = ec2.MachineImage.generic_linux({
            "us-east-1": "ami-01cc34ab2709337aa"
        })

        instance1 = ec2.Instance(self, "web1",
                                 instance_type=ec2.InstanceType(instance_type.value_as_string),
                                 machine_image=ami_linux,
                                 vpc=vpc,
                                 vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
                                 key_pair=ec2.KeyPair.from_key_pair_name(self, "KeyPairName1", key_pair_name.value_as_string),
                                 security_group=sg)

        instance2 = ec2.Instance(self, "web2",
                                 instance_type=ec2.InstanceType(instance_type.value_as_string),
                                 machine_image=ami_linux,
                                 vpc=vpc,
                                 vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
                                 key_pair=ec2.KeyPair.from_key_pair_name(self, "KeyPairName2", key_pair_name.value_as_string),
                                 security_group=sg)

        lb = elbv2.ApplicationLoadBalancer(self, "EngineeringLB",
                                           vpc=vpc,
                                           internet_facing=True)
        listener = lb.add_listener("Listener", port=80)
        target_group = elbv2.ApplicationTargetGroup(self, "TargetGroup",
                                                    vpc=vpc,
                                                    port=80,
                                                    target_type=elbv2.TargetType.INSTANCE)
        target_group.add_targets("InstanceTargets",
                                 targets=[instance1, instance2])
        listener.add_target_groups("TargetGroupListener", target_groups=[target_group])

        CfnOutput(self, "WebUrl",
                  value=lb.load_balancer_dns_name,
                  description="DNS of the load balancer")

app = App()
AlbCdkStack(app, "AlbCdkStack")
app.synth()
