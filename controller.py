from kubernetes import client, config, watch






if __name__ == "__main__":
    config.load_kube_config()
    