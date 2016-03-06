import  argparse
import  configparser
import 	datetime
import	onedrivesdk
from	onedrivesdk.helpers import GetAuthCodeServer
import	os

def main():
	print("Note: if not a clean directory, files may get overwritten depending on file names (and dates)!")
	where_to_store_files = input("Give me the path to store files: ")

	redirect_uri = "http://localhost:8080/"
	client_secret = "Hiwam3I396T7ejmI-qku76Zby6kAwZcD"
	client = onedrivesdk.get_default_client(client_id="00000000401871C6", scopes = ['wl.signin', 'wl.offline_access', "onedrive.readwrite"])
	auth_url = client.auth_provider.get_auth_url(redirect_uri)
	code = GetAuthCodeServer.get_auth_code(auth_url, redirect_uri) # get the code
	client.auth_provider.authenticate(code, redirect_uri, client_secret)

	directories = ["root"]
	id_list = ["root"]

	items = getChildren(client, id_list[-1])

	to_sync = (navigate(client, directories, id_list, items))
	
	while(True):
		sync(client, to_sync, where_to_store_files)

def argparse():
	parser = argparse.ArgumentParser(description='Sync folders between onedrive and your local drive.')
def getChildren(client, item_id):
	return client.item(id=item_id).children.get()

def navigate(client, directories, id_list, dir_contents):
	os.system('cls' if os.name == 'nt' else 'clear')
	print("What folder would you like to sync?")
	count = 0
	folders = []
	directory = concatList(directories)
	print("{} {} (current folder)".format(count, directory))
	folders.append(directory)
	count += 1

	print("folders in " + directory)
	for item in dir_contents:
		if(item.folder != None):
			folders.append(item)
			print("{} {}".format(count, item.name))
			count += 1

	print("files in " + directory)
	for item in dir_contents:
		if(item.file != None):
			print("{}".format(item.name))

	if(len(folders) > 0):
		folder = input("What folder would you like to select (-1 to go up a dir, 0 to sync current)")
		folder = int(folder)
		if(0 < folder and folder <= len(folders)):

			printOptions()
			option = int(input())

			if(option == 0):
				print("returning " + folders[folder].name)
				return folders[folder].id

			elif(option == 1):
				directories.append(folders[folder].name)
				items = getChildren(client, folders[folder].id)
				id_list.append(folders[folder].id)
				return navigate(client, directories, id_list, items)
		elif(0 == folder):
			print(id_list)
			return id_list[-1]
		elif(-1 == folder):
			directories = directories[:-1]
			id_list = id_list[:-1]
			items = getChildren(client, id_list[-1])
			return navigate(client, directories, id_list, items) 

		else:
			print("You selected {}".format(folder))
			print("There are {} folders".format(len(folders)))


	else:
		print("0: select current file to sync")
		print("1: go up a dir")
		choice = int(input())
		if(choice == 0):
			print(id_list[-1])
			return id_list[-1]
		elif(choice == 1):
			directories = directories[:-1]
			id_list = id_list[:-1]
			items = getChildren(client, id_list[-1])
			return navigate(client, directories, id_list, items) 

def concatList(l):
	to_ret = l[0]
	for dir in l[1:]:
		to_ret += "/" + dir
	return to_ret

def printOptions():
	print("0: select as folder to sync")
	print("1: traverse into folder")

def sync(client, item_id, directory, files_only=False):
	have_children = False
	tries = 0
	items_in_onedrive_folder = None
	while(not have_children and tries < 3):
		try:
			items_in_onedrive_folder = getChildren(client, item_id)
			have_children = True
		except:
			have_children = False
			tries += 1
			print("Couldn't get sync files...")
			print("Attempt " + str(tries) + " of 3...")
	#unable to get children...
	if(items_in_onedrive_folder == None):
		return 
	items_in_onedrive_names = []
	items_in_drive_folder= []
	print("Currently syncing folder {}".format(directory))

	#Download items w/in the onedrive folder
	for item in items_in_onedrive_folder:
		items_in_onedrive_names.append(item.name)
		if(item.folder != None and not files_only):
			mkdir(directory + "/" +item.name)
			sync(client, item.id, directory + "/" +item.name)
		elif(item.folder != None and files_only):
			mkdir(directory + "/" +item.name)
			sync(client, item.id, directory + "/" +item.name)
		elif(item.file != None):
			if(not os.path.isfile(directory + "/" + item.name)):
				client.item(id=item.id).download(directory + "/" + item.name)

	#Upload files that are on local drive and not in onedrive
	items_in_drive_folder = [file for file in os.listdir(directory) if os.path.isfile(directory + "/" + file)]
	folders_in_drive_folder = [folder for folder in os.listdir(directory) if os.path.isdir(directory + "/" + folder)]
	print(items_in_drive_folder)
	print(folders_in_drive_folder)
	for item_on_drive in items_in_drive_folder:
		#print(item_on_drive)
		if(item_on_drive not in items_in_onedrive_names):
			print("Trying to add file " + item_on_drive)
			tries = 0
			upload_comp = False
			while(not upload_comp and tries < 3):
				try:
					client.item(id=item_id).children[item_on_drive].upload(directory + "/" + item_on_drive)
					upload_comp = True
				except:
					upload_comp = False
					tries +=1
					print("Couldn't upload file " + item_on_drive + "...")
					print("Attempt " + str(tries) + " out of 3")
	for folder_on_drive in folders_in_drive_folder:

		if(folder_on_drive not in items_in_onedrive_names):
			f = onedrivesdk.Folder()
			i = onedrivesdk.Item()
			i.name = folder_on_drive
			i.folder = f
			print("Trying to add folder " + i.name)
			
			
			tries = 0
			upload_comp = False
			while(not upload_comp and tries < 3):
				try:
					client.item(drive="me", id=item_id).children.add(i)
					upload_comp = True
				except:
					upload_comp = False
					tries +=1
					print("Couldn't upload folder " + folder_on_drive + "...")
					print("Attempt " + str(tries) + " out of 3")
			if(upload_comp):
				sync(client, i.id, directory + i.name)
	
def mkdir(path):
	try:
		os.mkdir(path)
	except:
		pass
if __name__ == "__main__":
	main()
