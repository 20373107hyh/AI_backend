import shutil

from apscheduler.schedulers.background import BackgroundScheduler

from teacher.models import Experiment
import docker
scheduler = BackgroundScheduler()

def delete_experiment(experiment_id):
    # 从数据库中删除实验的逻辑
    experiment = Experiment.objects.get(id=experiment_id)
    container_name = 'experiment_' + str(experiment_id)
    client = docker.from_env()
    container = client.containers.get(container_name)
    container.stop()
    container.remove()
    container_path = './users_' + str(experiment.user_id.user_id) + '/container_experiment_' + experiment_id
    shutil.rmtree(container_path)
    experiment.delete()
    print(f'Experiment {experiment_id} deleted.')