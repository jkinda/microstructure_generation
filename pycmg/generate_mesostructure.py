# -*- coding: utf-8 -*-

import numpy as np

class Mesostructure:
    ''' This class generates micro/mesostructure by assembling the inclusion/aggregates on to the main micro/mesostructure

    Parameters
    ----------
    mesostructure_size:   array of size (3), type int
                          Size of the mesostructure 3D matrix.
    configuration:        Configuration object
                          Configuration object which provides details about the aggregate type and size distribution for assembly.

    '''
    def __init__(self,mesostructure_size=[100,100,100], configuration=None):
        self.size = np.array(mesostructure_size).astype(int)
        self.configuration = []
        self.vf_max = []; self.vf = []; self.attempt = []
        config = []
        config.append(configuration)
        if configuration is not None:
            self.configuration.extend(config)
            
        for i in range(len(self.configuration)):
            self.vf_max.append(self.configuration[i].vf_max_assembly)
        if np.sum(self.size != 0) != 3:
            raise Exception('Assembly size is invalid')
        self.inclusionList = []
        self.conf_count = 0
        self.n_inc_total = []
        self.mat_meso = np.zeros((self.size)).astype(int)
        self.vf_previous = 0
            
    
    def add_configuration(self, configuration):
        '''
        Add inclusion configuration to the assembly.
        
        Parameters
        ----------
        configuration:   Configuration object
                         Configuration object which provides details about the aggregate type and size distribution for assembly.
                         
        '''
        config = []
        config.append(configuration)
        self.configuration.extend(config)
        for i in range(len(config)):
            self.vf_max.append(config[i].vf_max_assembly)
    
    def assemble_SRA(self, attempt_max=500000, threshold=50, iter_limit=10):
        '''
        Assemble aggregates/pores onto the mesostructure 3D matrix using Semi-Random Assembly (SRA) algorithm.

        Parameters
        ----------
        attempt_max:    int, default:50000
                        Maximum number of unsuccessfull assembly attempts before temrinating the assembly algorithm.
        threshold:      int, default:50
                        Number of unsuccessfull attempts after which the algorithm shifts to SRA (alorithm type-2) from RSA (algorithm type-1)
        iter_limit:     int, default:10
                        Number of unsuccessfull attempts to try with the same particle/aggregate orientation before switching to another random orientation.
                        
        Return
        ------
        mat_meso:       3D array of type int
                        Mesostructure 3D array with aggregates/pores/particles assembled inside.
        '''
        
        if len(self.configuration) == 0:
            raise Exception('No configuration is loaded')
            
        if len(self.configuration[self.conf_count].inclusionFamList) == 0:
            raise Exception('No inputs are given for the configuration. You can provide default inputs by using load_inclusion() method in Configuration class!')

        if np.sum(self.vf_max) > 1:
            raise Exception('Maximum volume fraction of the aggregates in the micro/mesostructure cannot be more than 1')
        
        
        assembly_vf_vox = np.size(self.mat_meso)
        inclusion_count = []
        vf_inc_max = 0
        for i in range(np.size(self.configuration[self.conf_count].inclusionFamList)):
            vf_inc_max += self.configuration[self.conf_count].inclusionFamList[i].vf_max
            self.configuration[self.conf_count].inclusionFamList[i].vf_each = float(self.configuration[self.conf_count].inclusionFamList[i].standard_inclusion.vol_vox)/float(assembly_vf_vox)
            self.configuration[self.conf_count].inclusionFamList[i].n_inclusion = int(round(float(self.configuration[self.conf_count].inclusionFamList[i].vf_max)*self.vf_max[self.conf_count]/self.configuration[self.conf_count].inclusionFamList[i].vf_each))
            inclusion_count.append(self.configuration[self.conf_count].inclusionFamList[i].n_inclusion)
            self.configuration[self.conf_count].inclusionFamList[i].count = 0
        
        vf_test=0
        for i in range(np.size(self.configuration[self.conf_count].inclusionFamList)):
            vf_test+=self.configuration[self.conf_count].inclusionFamList[i].n_inclusion*self.configuration[self.conf_count].inclusionFamList[i].vf_each
        if vf_inc_max <= 1-10E-3 or vf_inc_max >= 1+10E-3:
            raise Exception('Total maximum volume fraction of all inclusion families must be close to 1')
        
        self.n_inc_total.append(np.sum(inclusion_count))
        inclusionFamList = self.configuration[self.conf_count].inclusionFamList
        sortedId = self.configuration[self.conf_count].inclusion_sorted
        algType = 1
        vf = 0; i = 0; attempt = 0; T = threshold
        vf_max = np.sum(self.vf_max[0:self.conf_count+1])
        vf_max_incFam = inclusionFamList[0].vf_max*vf_max
        inclusionList = []
        while vf < vf_max and i < np.size(inclusionFamList) and attempt <= attempt_max:
            inclusion = inclusionFamList[sortedId[i]].generate_inclusion()
            iteration = 0
            if attempt > T:
                algType = 2
            else:
                algType = 1
            
            accept = 0
            while accept == 0 and iteration < iter_limit and attempt <= attempt_max:
                iteration = iteration+1
                x0 = np.floor(np.random.random(3)*self.size).astype(int)
                if self.mat_meso[x0[0],x0[1],x0[2]] == 0:
                    self.mat_meso,inclusion,check = self.__assemble_inclusion(self.mat_meso, inclusion, x0)
                    if check == True:
                        accept = 1
                        inclusion.x0 = np.copy(x0)
                    else:
                        accept = 0
                        attempt = attempt+1
                        while accept == 0 and iteration <= iter_limit and attempt <= attempt_max and algType == 2:
                            iteration = iteration+1
                            x0 = np.round(np.random.random(3)*self.size).astype(int)
                            direction = np.random.permutation(3)
                            while accept == 0 and x0[direction[1]] <= self.size[direction[1]] and attempt <= attempt_max:
                                while accept == 0 and x0[direction[0]] <= self.size[direction[0]] and attempt <= attempt_max:
                                    self.mat_meso,inclusion,check = self.__assemble_inclusion(self.mat_meso, inclusion, x0)
                                    if check is True:
                                        accept = 1
                                        inclusion.x0 = np.copy(x0)
                                    
                                    else:
                                        x0[direction[0]] += 1
                                        attempt += 1
                                
                                x0[direction[0]] = 0
                                x0[direction[1]] += 1
                else:
                    attempt += 1
                    
            if accept == 1:
                inclusionList.append(inclusion)
                inclusionFamList[sortedId[i]].inclusionList.append(inclusion)
                inclusionFamList[sortedId[i]].count += 1
                inclusion.vol_vox = np.sum(inclusion.mat_inc == inclusion.vox_inc)+np.sum(inclusion.mat_inc==inclusion.vox_coat)
                inclusion.vf_each = inclusion.vol_vox/np.size(self.mat_meso)
                inclusionFamList[i].vf += inclusion.vf_each
                vf = np.sum(np.logical_and(self.mat_meso != 0, self.mat_meso != inclusionFamList[i].vox_space)) / np.size(self.mat_meso)
                T=threshold
                iteration = 0
                accept = 0
                attempt = 0
                if inclusionFamList[sortedId[i]].count >= inclusionFamList[sortedId[i]].n_inclusion or inclusionFamList[sortedId[i]].vf>=vf_max_incFam:
                    i += 1 
                    if i < np.size(inclusionFamList):
                        vf_max_incFam = inclusionFamList[sortedId[i]].vf_max*vf_max

        self.vf.append(vf); self.attempt.append(attempt)
        self.inclusionList.append(inclusionList)
        self.conf_count += 1
        print('Configuration {0} is assembled with volume fraction {1}'.format(self.conf_count,vf-self.vf_previous))
        self.vf_previous += vf
        return self.mat_meso
                   
    def __assemble_inclusion(self, mat_meso, inclusion, x0):
        check = False
        indices = lambda x_start, x_end, length: np.mod(np.arange(x_start, x_end+1), length).astype(int)
        inclusion_size = np.array(np.shape(inclusion.mat_inc))
        ind_start = x0-np.floor(inclusion_size/2)
        ind_end = x0+np.ceil(inclusion_size/2)-1
        ix = indices(ind_start[0], ind_end[0], self.size[0])
        iy = indices(ind_start[1], ind_end[1], self.size[1])
        iz = indices(ind_start[2], ind_end[2], self.size[2])
        [x, y, z] = np.meshgrid(ix, iy, iz)
        mat_test = mat_meso[x, y, z]
        if np.sum(mat_test[inclusion.mat_inc > 0]) == 0:
            mat_test[inclusion.mat_inc > 0] = inclusion.mat_inc[inclusion.mat_inc > 0]
            mat_meso[x, y, z] = mat_test
            check = True
        return mat_meso, inclusion, check

        
       
        

                        