import tempfile
from sqlalchemy import (Table, Column, Integer, Float, String, Sequence, BLOB,
                        MetaData, ForeignKey, create_engine, select,
                        UniqueConstraint)
import os
import os.path
import uuid
import json
import numpy.distutils.cpuinfo as cpuinfo
import pandas as pd
from abc import ABCMeta, abstractmethod, abstractproperty
import six
multi_processing = True # use False only for debug!

if multi_processing:
    from multiprocessing import Process
else:
    class Process(object):
        def __init__(self, target, args):
            target(*args)
        def start(self):
            pass
        def join(self):
            pass
        
def get_cpu_info():
    return json.dumps(cpuinfo.cpu.info)


def table_exists(tbl, conn):
    cur = conn.cursor()
    return list(cur.execute(
        """SELECT name FROM sqlite_master WHERE type=? AND name=?""",
        ('table', tbl)))

def describe_table(tbl, conn):
    cur = conn.cursor()
    return list(c.execute("PRAGMA table_info([{}])".format(tbl)))

def dump_table(table, db_name):
    #lst_table=['bench_tbl', 'case_tbl','measurement_tbl']
    engine = create_engine('sqlite:///' + db_name, echo=False)
    metadata = MetaData(bind=engine)
    tbl = Table(table, metadata, autoload=True)
    conn = engine.connect()
    #print(metadata.tables[tbl])
    s = tbl.select() #select([[tbl]])
    df =  pd.read_sql_query(s, conn)
    print(df)


    
class BenchEnvBase(six.with_metaclass(ABCMeta, object)):
    def __init__(self, db_name=None, append_mode=True, drop_existing_db=False):
        if db_name is None:
            _, self._db_name = tempfile.mkstemp(prefix='benchmarkit_', suffix='.db')
        else:
            if drop_existing_db and os.path.isfile(db_name):
                os.remove(db_name)
            self._db_name = db_name
        #import pdb; pdb.set_trace()
        self._engine = create_engine('sqlite:///' + self.db_name, echo=False)
        self._metadata = MetaData(bind=self._engine)
        self._append_mode = append_mode        
        self.create_tables_if()

    @property
    def engine(self):
        return self._engine

    @property
    def db_name(self):
        return self._db_name

    @abstractmethod
    def create_tables_if(self):
        pass

class BenchEnv(BenchEnvBase):
    """
    NB: BenchEnv and its subclasses are singletons
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(BenchEnv, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self, db_name=None, append_mode=True, drop_existing_db=False):
        self._bench_tbl = None
        self._case_tbl = None
        self._measurement_tbl = None
        super(BenchEnv, self).__init(db_name, append_mode, drop_existing_db)
        
    @property
    def bench_tbl(self):
        return self._bench_tbl

    @property
    def measurement_tbl(self):
        return self._measurement_tbl

    @property
    def bench_list(self):
        tbl = self._bench_tbl
        s = (select([tbl]).with_only_columns([tbl.c.name]))
        with self.engine.connect() as conn:
            rows = conn.execute(s).fetchall()
            return [e[0] for e in rows] 

    def create_tables_if(self):
        if 'bench_tbl' in self.engine.table_names():
            self._bench_tbl = Table('bench_tbl', self._metadata, autoload=True)
            self._case_tbl = Table('case_tbl', self._metadata, autoload=True)
            self._measurement_tbl = Table('measurement_tbl', self._metadata, autoload=True)
            return
        self._bench_tbl = Table('bench_tbl', self._metadata,
                                Column('id', Integer, Sequence('bench_id_seq'), primary_key=True),                                
                                Column('name', String, unique=True),
                                Column('description', String),
                                Column('step_header', String),                                
                                Column('py_version', String),
                                Column('py_compiler', String),
                                Column('py_platform', String),
                                Column('py_impl', String),                                
                                Column('cpu_info', String),

                                autoload=False)
        self._case_tbl = Table('case_tbl', self._metadata,
                               Column('id', Integer, Sequence('case_id_seq'), primary_key=True),                                
                               Column('name', String),
                               Column('bench_id', Integer, ForeignKey('bench_tbl.id')),
                               Column('corrected_by', Integer), # TODO: ref integrity
                               Column('description', String),
                               UniqueConstraint('name', 'bench_id', name='uc1'),
                               autoload=False)
        self._measurement_tbl = Table('measurement_tbl', self._metadata,
                                      Column('id', Integer, Sequence('m_id_seq'), primary_key=True),
                                      Column('case_id', Integer),
                                      Column('i_th', Integer),
                                      Column('step',  Integer),                                      
                                      Column('step_info', String),
                                      Column('mem_usage',  Float),
                                      Column('elapsed_time',  Float),
                                      Column('sys_time',  Float),
                                      Column('user_time',  Float),
                                      Column('ld_avg_1',  Float),
                                      Column('ld_avg_5',  Float),
                                      Column('ld_avg_15',  Float),
                                      Column('prof',  BLOB),
                                      UniqueConstraint('case_id', 'step', 'i_th', name='uc2'),
                                       autoload=False)
    
        self._metadata.create_all(self._engine, checkfirst=self._append_mode)


class RunStepBenchEnv(BenchEnvBase):
    def __init__(self, db_name=None, append_mode=True, drop_existing_db=False):
        self._run_step_bench_tbl = None
        super(RunStepBenchEnv, self).__init__(db_name, append_mode, drop_existing_db)
    def create_tables_if(self):
        if 'run_step_bench_tbl' in self.engine.table_names():
            self._run_step_bench_tbl = Table('run_step_bench_tbl', self._metadata, autoload=True)
            return
        self._run_step_bench_tbl = Table('run_step_bench_tbl', self._metadata,
                                      Column('id', Integer, Sequence('m_id_seq'), primary_key=True),
                                      Column('module_id', String),
                                      Column('run_number', Integer),
                                      Column('step_size', Integer),
                                      Column('howlong', Integer),
                                      Column('next_state', Integer),                                      
                                      Column('steps_run', Integer),
                                      Column('reads', Integer),
                                      Column('updates', Integer),
                                      Column('creates', Integer),                                      
                                      Column('elapsed_time',  Float),
                                      Column('sys_time',  Float),
                                      Column('user_time',  Float),
                                      Column('ld_avg_1',  Float),
                                      Column('ld_avg_5',  Float),
                                      Column('ld_avg_15',  Float),
                                       autoload=False)
    
        self._metadata.create_all(self._engine, checkfirst=self._append_mode)

    @property
    def bench_table(self):
        return self._run_step_bench_tbl
    def dump(self):
        dump_table(self.bench_table, self.db_name)
        
def get_random_name(prefix):
    return prefix+str(uuid.uuid4()).split('-')[-1]


def banner(s, c='='):
    hr = c*(len(s) + 2) + '\n'
    s2 = ' ' + s + ' \n'
    return hr + s2 + hr

def print_banner(s, c='='):
    print(banner(s, c))
    
