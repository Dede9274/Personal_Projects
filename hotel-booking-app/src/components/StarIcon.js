import React from 'react';
import {MaterialCommunityIcons} from '@expo/vector-icons';

const StarIcon = ({name = 'star', size = 19}) => (
  <MaterialCommunityIcons name={name} color="#F59E0B" size={size} />
);

export default StarIcon;
