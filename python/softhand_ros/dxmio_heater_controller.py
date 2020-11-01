import math

import rospy

from dynamixel_driver.dynamixel_const import *

from dynamixel_controllers.srv import SetSpeed
from dynamixel_controllers.srv import TorqueEnable
from dynamixel_controllers.srv import SetComplianceSlope
from dynamixel_controllers.srv import SetComplianceMargin
from dynamixel_controllers.srv import SetCompliancePunch
from dynamixel_controllers.srv import SetTorqueLimit

from std_msgs.msg import Float64
from dynamixel_msgs.msg import MotorStateList
from dynamixel_msgs.msg import JointState


# Control Table Constants for DXMIO
DXMIO_PWM_DUTY_0 = 22
DXMIO_PWM_DUTY_1 = 24
DXMIO_PWM_DUTY_2 = 26


class DxmioHeaterController(object):
    # initialize, start, stop
    def __init__(self, dxl_io, controller_namespace, port_namespace):
        self.running = False
        self.dxl_io = dxl_io
        self.controller_namespace = controller_namespace
        self.port_namespace = port_namespace
        self.joint_name = rospy.get_param(self.controller_namespace + '/joint_name')

        # joint_state
        self.joint_state = JointState(name=self.joint_name, motor_ids=[self.motor_id])

    def initialize(self):
        raise NotImplementedError

    def start(self):
        self.running = True
        self.joint_state_pub = rospy.Publisher(self.controller_namespace + '/state', JointState, queue_size=1)
        self.command1_sub = rospy.Subscriber(self.controller_namespace + '/command1', Float64, self.process_command1)
        self.command2_sub = rospy.Subscriber(self.controller_namespace + '/command2', Float64, self.process_command2)
        self.command3_sub = rospy.Subscriber(self.controller_namespace + '/command3', Float64, self.process_command3)        

    def stop(self):
        self.running = False
        self.joint_state_pub.unregister()
        self.motor_states_sub.unregister()
        self.command_sub.unregister()
        self.speed_service.shutdown('normal shutdown')
        self.torque_service.shutdown('normal shutdown')
        self.compliance_slope_service.shutdown('normal shutdown')

    def set_pwm_duty(self, address, pwm_duty):
        sid = self.motor_id
        pwm_duty = min (pwm_duty, 0.1) # PWM duty limit for circuit protection
        pwm_duty *= 65535 # PWM duty conversion 1.0 -> 65535
        pwm_duty &= 0xffff
        loVal = int(pwm_duty % 256) # split pwm_duty into 2 bytes
        hiVal = int(pwm_duty >> 8)
        writeableVals = [] # prepare value tuples for call to syncwrite
        writeableVals.append( (sid, loVal, hiVal) )
        self.sync_write(address, writeableVals) # use sync write to broadcast multi servo message

    def process_command1(self, msg):
        self.set_pwm_duty(DXMIO_PWM_DUTY_0, msg.data)

    def process_command2(self, msg):
        self.set_pwm_duty(DXMIO_PWM_DUTY_1, msg.data)

    def process_command3(self, msg):
        self.set_pwm_duty(DXMIO_PWM_DUTY_2, msg.data)
