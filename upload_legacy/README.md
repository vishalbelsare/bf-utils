##Pre-requisites
After [pennsieve installation](https://docs.pennsieve.io/docs/the-pennsieve-agent), set [configuration](https://docs.pennsieve.io/docs/configuring-the-client-credentials)

##Steps
1. make sure the "HPAP.list.txt" file has the donor info
2. create a data folder for the donor you need to upload data for, with the name "[DONOR-ID].[Datatype]", e.g. "HPAP-022.mrna"
3. Run python code, e.g. `python BF.upload.py HPAP-022.mrna`
4. The data will be uploaded to Pennsieve under the root directory for the donor.
