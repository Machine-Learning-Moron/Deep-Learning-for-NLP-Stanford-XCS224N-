
# Preparing environment in Host
# ------------------------------

# SSH into your machine
export SSH_USER=pablo
export SSH_HOST=10.99.195.149

export KEY_PATH="/mnt/c/Users/RUIZP4/Documents/DOCS/RnD/id_rsa_BASF_RnD"
export LOCAL_PROJECT_PATH="/mnt/c/Users/RUIZP4/Documents/DOCS/Pablo_Personal/StanfordNLP/Side_projects/Document_Clustering"
export REMOTE_PROJECT_PATH="/home/pablo/Side_NLP_Tests/"
export EXCLUDE_SYNC_FILE="exclude_sync.txt"

# Push to remote
rsync -auv -e "ssh -i ${KEY_PATH}" \
    --exclude-from=${EXCLUDE_SYNC_FILE} \
    $LOCAL_PROJECT_PATH ${SSH_USER}@${SSH_HOST}:$REMOTE_PROJECT_PATH

# SSH Connect
ssh -i ${KEY_PATH} ${SSH_USER}@${SSH_HOST}

# Open LocalForwarding on the Background
ssh -i $KEY_PATH \
    -fNL 8889:127.0.0.1:18889 \
    -fNL 8899:127.0.0.1:18899 \
    -fNL 8999:127.0.0.1:18999 \
    -fNL 9999:127.0.0.1:19999 \
    pablo@10.99.195.149

    
# Using Docker in Host
# ---------------------

export DOCKER_PORT=8889
export CLUSTER_PORT=18889

export P21=8899
export P22=18899
export P31=8999
export P32=18999
export P41=9999
export P42=19999

export DOCKER_IMAGE=pablorr10/nlp:minimal
export CONTAINER_NAME=nlpminimal

export CLUSTER_ROOT=/home/pablo/Side_NLP_Tests/Document_Clustering
export CONTAINER_ROOT=/app

export CLUSTER_DATA=/datadrive/madrid
export CONTAINER_DATA=${CONTAINER_ROOT}/globaldata

# Open a shell in the container
docker stop ${CONTAINER_NAME} || true
docker run --rm -dit \
    --name ${CONTAINER_NAME} \
    -p ${CLUSTER_PORT}:${DOCKER_PORT} \
    -p ${P21}:${P22} \
    -p ${P31}:${P32} \
    -p ${P41}:${P42} \
    -v ${CLUSTER_ROOT}:${CONTAINER_ROOT} \
    -v ${CLUSTER_DATA}:${CONTAINER_DATA} \
    ${DOCKER_IMAGE} jupyter contrib nbextension install --user # Rebuild image

docker logs ${CONTAINER_NAME}

docker exec -it ${CONTAINER_NAME} bash

# Move from Remote to Host --> (Notebooks develped in remote bring to host to add it to Git)
export REMOTE_DIR="/home/pablo/NLP/jupyter_notebooks"
export LOCAL_DIR="/mnt/c/Users/RUIZP4/Documents/DOCS/RnD/NLP/jupyter_notebooks/"

scp -i ${KEY_PATH} \
    -r ${SSH_USER}@${SSH_HOST}:${REMOTE_DIR} ${LOCAL_DIR}



