#!/usr/bin/env python3

# Legacy code that was based on:
# https://github.com/faryabiLab/hpap-projects/blob/master/2019%20Projects/\
# 2019-06-12_IMC-upload/2019-06-12_IMC-upload-notebook.ipynb

import pandas as pd
from sqlalchemy import create_engine
from blackfynn import Blackfynn
import os
import tqdm
from tqdm import tqdm_notebook

bf = Blackfynn()

# Sql credentials
sql_user = 'xxx'   # dhu: MySQL username masked
sql_pass = r'xxx'  # dhu: MySQL password masked

# Forwarded port to production sql server
sql_port = 3306

engine = create_engine(
    "mysql+mysqlconnector://" + sql_user + ":" + sql_pass + "@127.0.0.1:" +
    str(sql_port) + "/hpap_records"
)

try:
    connection = engine.connect()
    connection.close()
    print("Connection successful!")
except Exception as e:
    print("Connection failed")
    print(e)

# Location where the files reside
imc_data_dir = "xxx"

file_dict = dict()
for path, dirs, files, in os.walk(imc_data_dir):
    if len(files) != 0:
        file_dict[path] = files

file_df = pd.DataFrame.from_dict(file_dict, orient="index").transpose().melt().dropna()
image_files = file_df[file_df.value.str.contains(".tiff")]

image_files.columns = ["path", "image_file"]
image_files.loc[:, 'donor'] = image_files['image_file'].str.split("_").str[0]
image_files.loc[:, 'anatomy'] = image_files['image_file'].str.split("_").str[2]
image_files.loc[:, 'region'] = image_files['image_file'].str.split("_").str[3]
image_files.loc[:, 'overlay'] = image_files['image_file'].str.split("_").str[4]
image_files.loc[:, 'conjugate'] = image_files['image_file'].str.split("_").str[5].str.split(".").str[0]

# Ignore overlays and files with "resumed" in their name
image_files = image_files[
    (image_files['path'].str.contains("original image files")) &
    (image_files['image_file'].str.contains("resumed") == False)
]

# Looks like some anatomy section wasn't determined. Let's maintain our naming
# for anatomy elements that are "unknown"
image_files.loc[:, 'anatomy'] = image_files['anatomy'].str.replace(
    "Indeterminate-of-pancreas", "Pancreas-unsure-of-orientation"
)

# Now that we've got all of the elements of the nomenclature identified, let's
# mock up their destination collection in blackfynn. After that we'll see if
# the collection exists at all.
def imc_collection_namer(donor, anatomy, roi):
    return "/" + donor + "/Imaging mass cytometry/" + anatomy.replace("-", " ") \
        + "/FFPE-Stain Panel 1/" + roi

image_files.loc[:, 'Colpath'] = image_files.apply(
    lambda row: imc_collection_namer(row['donor'], row['anatomy'], row['region']), axis=1
)

# Since we've got the destination collections mocked up, let's see if they
# actually exist
conn = engine.connect()

collection_df = pd.read_sql(
    "SELECT * " +
    "FROM hpap_records.blackfynn_collection_index " +
    "WHERE Colpath LIKE \"%Imaging mass cytometry%\"",
    con=conn
)

package_df = pd.read_sql(
    "SELECT * " +
    "FROM hpap_records.blackfynn_data_index " +
    "WHERE Colpath LIKE \"%Imaging mass cytometry%\"",
    con=conn
)

conn.close()

# Ensure we're only uploading files that haven't made it to Blackfynn yet
new_files_df = image_files[
    image_files.image_file.isin(package_df.Filename.values.tolist())== False
]

upload_df = new_files_df.merge(
    collection_df[['Colpath', 'Colid']], on=['Colpath'], how='left'
)

# Expand that list to include the upper level collections, so we don't miss
# anything (ex: "/HPAP-001/Imaging mass cytometry/Pancreas-unsure-of-orientation")
def get_all_subcollections(missing_collections):
    return_set = set()
    for col in missing_collections:
        # We're going to assume the dataset is created and
        # the Imaging mass cytometry folder has been made
        split_col = col.split("/", 3)
        # Get the "head" of the collection
        head = "/".join(split_col[:3]) + '/'
        # Isolate the new collections to be made
        sub_folders = split_col[-1].split("/")
        # Iterate through the list of extra collections, elongating with each iteration
        for i in range(1, len(sub_folders) + 1):
            new_collection = head + "/".join(sub_folders[:i])
            if new_collection not in return_set:
                return_set.add(new_collection)

    return return_set

# All subfolders needed to upload these new files
potential_new_collections = sorted(
    list(
        get_all_subcollections(upload_df.Colpath.unique().tolist())
    )

)

new_collections = sorted([
    x for x in potential_new_collections
    if x not in collection_df.Colpath.values.tolist()
])

dsets = {entry.name.split(" ")[0]: entry.id for entry in bf.datasets()}

def make_blackfynn_collection(donor, collection):
    global collection_df

    # Do not make duplicates
    if collection in collection_df.Colpath.values.tolist():
        return True

    # For collections near the top
    if "FFPE" not in collection:
        parent_dset = bf.get_dataset(dsets.get(donor))
        parent_col = [x for x in parent_dset.items if x.name == "Imaging mass cytometry"][0]
        parent_name = parent_col.name
        parent_id = parent_col.id
    # For collections not near the top
    else:
        parent_name = collection.rsplit("/", 1)[0]
        parent_id = collection_df[collection_df['Colpath'] == parent_name]['Colid'].values.tolist()[0]

    # We're not making the full collection path into a collection name.
    # Just the next "step" in the directory path
    new_collection_name = collection.split(parent_name)[1].split('/')[1]

    # Make the collection in the parent col
    parent_obj = bf.get(parent_id)
    if new_collection_name not in [x.name for x in parent_obj.items]:
        new_collection_name = collection.split(parent_name)[1].split('/')[1]
        parent_obj.create_collection(new_collection_name)
        parent_obj.update()

    # Record the collection in the collection_df so following collections
    # can lookup the new collections made.
    if collection not in collection_df.Colpath.values.tolist():
        # Dataset, Colname, Colpath, Colid
        new_collection_id = [x.id for x in parent_obj.items if x.name == new_collection_name][0]
        new_series = pd.Series(
            [donor, new_collection_name, collection, new_collection_id],
            index=["Dataset", "Colname", "Colpath", "Colid"]
        )
        collection_df = collection_df.append(new_series, ignore_index=True)

    # Sanity check
    new_collection_id = collection_df[collection_df['Colpath'] == collection]['Colid'].values.tolist()[0]
    new_collection_obj = bf.get(new_collection_id)

    return new_collection_obj.name == new_collection_name and collection in collection_df.Colpath.tolist()


"""
test_donor_1 = new_collections[0].split('/', 2)[1]
test_col_1 = new_collections[0]

test_donor_2 = new_collections[1].split('/', 2)[1]
test_col_2 = new_collections[1]

make_blackfynn_collection(test_donor_1, test_col_1)
make_blackfynn_collection(test_donor_2, test_col_2)
"""

results = []
for col in new_collections:
    donor = col.split('/', 2)[1]
    results.append(make_blackfynn_collection(donor, col))

# Now check that all files to be uploaded have a location to go to
actual_upload_df = new_files_df.merge(collection_df[['Colpath', 'Colid']], on=['Colpath'], how='left')

# Ensure there's a proper rename if need be
def imc_renamer(row):
    return "_".join(
        [
            row['donor'], "IMC", row['anatomy'], row['region'], row['overlay'],
            row['conjugate']
        ]
    )

actual_upload_df.loc[:, 'rename'] = actual_upload_df.apply(imc_renamer, axis=1)

# Proceed with uploading
# ----------------------
pbar = tqdm_notebook(actual_upload_df)

def upload_IMC_file(row):
    global pbar
    try:
        file_path = row['image_file']
        file_name = os.path.splitext(file_path)[0]
        new_pack_name = row['rename']
        file_path = row['path'] + "\\" + row['image_file']
        parent_id = row['Colid']
        parent_obj = bf.get(parent_id)
        parent_packages = [x.name for x in parent_obj.items]

        # If the renamed package is present, stop
        if new_pack_name in parent_packages:
            pbar.update(1)
            return True

        # If neither the file or package are in the parent packages
        elif file_name not in parent_packages and new_pack_name not in parent_packages:
            parent_obj.upload(file_path)
            parent_obj.update()
            parent_packages = [x.name for x in parent_obj.items]

        # If the file name is present, rename it
        if file_name in parent_packages:
            file_obj = [x for x in parent_obj.items if x.name == file_name][0]
            file_obj.name = new_pack_name
            file_obj.update()
            parent_obj.update()
            pbar.update(1)

        return True

    except Exception as e:
        pbar.update(1)
        return False

actual_upload_df.loc[:, 'uploaded_and_renamed'] = actual_upload_df.apply(upload_IMC_file, axis=1)
actual_upload_df['uploaded_and_renamed'].all()

# Failed uploads
failed_uploads = actual_upload_df[actual_upload_df['uploaded_and_renamed'] == False]

# Upload the failed ones again
pbar = tqdm_notebook(failed_uploads)
failed_uploads.loc[:, 'uploaded_and_renamed'] = failed_uploads.apply(upload_IMC_file, axis=1)
