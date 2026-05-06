package net.fruadly.learningservice.dto;


import lombok.Data;
import net.fruadly.learningservice.entity.Resource;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.UUID;

@Data
public class ChapitrDto {
    private UUID id;
    private String title;
    private Date dateChapitre;
    private List<Resource> resources = new ArrayList<>();
}
