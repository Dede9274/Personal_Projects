import React from 'react';
import {MaterialCommunityIcons} from '@expo/vector-icons';

const BackIcon = ({name = 'chevron-left', color = '#344054', size = 34}) => (
  <MaterialCommunityIcons name={name} color={color} size={size} />
);

export default BackIcon;
