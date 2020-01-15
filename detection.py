import cv2, keyboard as kb, time, os
from serial import Serial
from math import sqrt

usb = "/dev/ttyACM0"


def getCascades():
	path = os.path.dirname(os.path.abspath(__file__))

	eye = cv2.CascadeClassifier()
	eye.load(cv2.samples.findFile(path+"/haarcascade_eye_tree_eyeglasses.xml"))
	
	face = cv2.CascadeClassifier()
	face.load(cv2.samples.findFile(path+"/haarcascade_frontalface_alt2.xml"))

	return {
		"eye": eye,
		"face": face
	}

def findFaces(frame):
	grayscale = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	grayscale = cv2.equalizeHist(grayscale)
	#-- Detect faces
	faces = cascades["face"].detectMultiScale(grayscale)
	for (x,y,w,h) in faces:
		center = (x + w//2, y + h//2)
		frame = cv2.ellipse(frame, center, (w//2, h//2), 0, 0, 360, (255, 0, 255), 4)
		frame = cv2.putText(frame, str((x, y))+str((w, h)), (x,y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255))
		# faceROI = grayscale[y:y+h,x:x+w]
		#-- In each face, detect eyes
		# eyes = cascades["eye"].detectMultiScale(faceROI)
		# for (x2,y2,w2,h2) in eyes:
		# 	eyeCenter = (x + x2 + w2//2, y + y2 + h2//2)
		# 	radius = int(round((w2 + h2)*0.25))
		# 	frame = cv2.circle(frame, eyeCenter, radius, (255, 0, 0 ), 4)

	# remove? same id?
	return frame, faces

def getMiddleFace(faces, camMaxes):
	middle = int(camMaxes[0] // 2), int(camMaxes[1] // 2)

	closest = (0, 0)
	closestDistance = sqrt(camMaxes[0]**2, camMaxes[1]**2) # set to max
	
	for x, y, w, h in faces:
		x, y = abs(x), abs(y)
		distance = sqrt(x**2 + y**2)
		if distance < closestDistance:
			closest = x, y
			closestDistance = distance

	return x, y


class Servos:
	LEFT = -1
	RIGHT = 1
	UP = -1
	DOWN = 1

	def __init__(self, serialObj, sensitivity=1):
		self.x, self.y = 0, 0
		self.calibrationPoint = None
		self.area = None
		self.serial = serialObj
		self.sensitivity = sensitivity


	def moveX(self, amount, direction):
		self.x += amount * direction
		self.updatePos()
	
	def moveY(self, amount, direction):
		self.x += amount * direction
		self.updatePos()

	def moveTo(self, x, y):
		self.x, self.y = x, y
		self.updatePos()


	def updatePos(self):
		# turn 60 into 060, for both angles
		x = "0"*(3-len(str(self.x))) + str(self.x)
		y = "0"*(3-len(str(self.y))) + str(self.y)
		# write to arduino
		self.serial.write(f"{x}{y}".encode())


	def getPos(self):
		return self.x, self.y


	def steer(self):
		if kb.is_pressed("left"):
			self.moveX(self.sensitivity, Servos.LEFT)
			
		if kb.is_pressed("right"):
			self.moveX(self.sensitivity, Servos.RIGHT)
			
		if kb.is_pressed("up"):
			self.moveY(self.sensitivity, Servos.UP)
		
		if kb.is_pressed("down"):
			self.moveY(self.sensitivity, Servos.DOWN)


	def getNewAngle(self, camCoords, camMaxes): # x, y, maxX, maxY
		# calculate calibration using the top left(p1) and bottom right(p2)
		# this is the area (in servo angles) that the servo should be limited to
		xPercent = camCoords[0] / camMaxes[0]
		yPercent = camCoords[1] / camMaxes[1]

		x = self.area[0] * xPercent + self.calibrationPoint[0]
		y = self.area[1] * yPercent + self.calibrationPoint[1]

		return x, y



def getFrame(cam):
	ret, frame = cap.read()
	if frame is None:
		exit("No frame")

	return frame

def main():
	serial = Serial(usb) #Serial(input("Serial port: "))
	servos = Servos(serial, sensitivity=0.5)
	cap = cv2.VideoCapture(0)

	if not cap.isOpened:
		print("Error opening video capture")
		exit(0)

	# CALIBRATION
	while True:
		points = []
		for i in range(2):
			while not kb.is_pressed("space"):
				frame = getFrame(cap)
				cv2.imshow("Calibrate servos", frame)
				# steer the servo
				servos.steer()

			points.append(servos.getPos())

			while kb.is_pressed("space"):
				pass

		# calculate calibration using the top left(p1) and bottom right(p2)
		# p2.x - p1.x, p2.y - p1.y
		p1, p2 = tuple(points)
		servos.calibrationPoint = p1
		# this is the area (in servo angles) that the servo should be limited to
		servos.area = p2[0] - p1[0], p2[1] - p1[1]


	while True:
		frame = getFrame(cap)
		frame, faces = findFaces(frame)

		x, y = getMiddleFace(faces)

		servos.moveTo(x, y)

		time.sleep(0.5)

		#cv2.imshow("dhfgjjsjsfgjhjghfdj", frame)

		# if cv2.waitKey(10) == 27:
		# 	break

if __name__ == '__main__':
	cascades = getCascades()
	main()