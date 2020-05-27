B
    ��[	  �               @   s�   d dl Z d dlZd dlZd dlZd dlmZmZmZm	Z	m
Z
 d dlmZ d dlmZ d dlmZ d dlmZ d dlmZ edd�Ze� d	d
� �Zeje	jge	jd�edd�dd� ��Zddd�Zdd� Ze� dd� �ZdS )�    N)�expose�worker�logger�settings�response)�Prodict)�
alru_cache)�HTTPServiceUnavailable)�count)�translit)�dbc               �   s   t t�� �� �S )N)�dict�enrich�
cache_info�_asdict� r   r   �main.pyr      s    r   )�keys�propsi   )�maxsizec              �   sf   y:| � dd �}tjst� �|r8tj� |�}|r8tf |�S i S  tk
r`   tjd|d� t�	� S X d S )N�ipzmmgeo error.)�location)
�get�stater   r	   �handle_location�	Exceptionr   �	exceptionr   �error)Zparamsr   r   r   r   r   r      s    
r   c             K   s�   t � }|r0|d d |_|d d |_|d |_| rtd| krt| d d |_d| d krb| d d nt| d d �|_|r�t|�dkr�|d }|d d |_d|d kr�|d d nt|d d �|_	|d |_
|S )N�namesZen�ruZiso_coder   )�pdictZ
country_enZ
country_ruZcountry_isoZcity_en�en_to_ruZcity_ru�lenZ	region_enZ	region_ruZ
region_iso)ZcityZcountryZsubdivisions�kwargs�resultZregionr   r   r   r   &   s     

r   c             C   s
   t | d�S )Nr   )r   )�textr   r   r   r!   9   s    r!   c              �   s�   ynt j�tj�std��t�tj�t_	t
�d� x:t� D ]0} t� I d H }t
jd| |d� t�d�I d H  q8W W n2 tjk
r�   Y n tk
r�   t
�d� Y nX d S )Nzdb file not foundz	DB loadedz
cache stat)Zloop�infoi,  z!error while opening database file)�os�path�isfiler   Zdb_file�FileNotFoundError�	maxminddbZopen_databaser   r   r   r&   r
   r   �asyncioZsleepZCancelledErrorr   r   )Znumr&   r   r   r   �loader=   s    
r-   )NNN)�
subprocess�os.pathr'   r+   r,   Zbandr   r   r   r   r   Zprodictr   r    Z	async_lrur   Zaiohttp.web_exceptionsr	   �	itertoolsr
   Ztransliterater   r   r   ZenricherZ
key_prefixr   r   r   r!   r-   r   r   r   r   �<module>   s    

